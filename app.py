from flask import Flask, render_template, jsonify, request, Response
import ipaddress
import os
import urllib.request
import urllib.parse
import json
from pathlib import Path
from datetime import datetime

import os
import sys

# When running this file directly (python backend/app.py), Python's import
# search may not include the project root, causing `import backend.*` to fail.
# Ensure the parent directory is on sys.path so package-style imports work.
if __name__ == "__main__" and __package__ is None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

from backend.config import Config
from backend.models import DB
from backend.routes.admin import admin_bp
from backend.routes.auth import auth_bp
from backend.routes.menu import MENU_SECTIONS, menu_bp
from backend.routes.orders import orders_bp
from backend.routes.reservation import reservation_bp


app = Flask(__name__, template_folder='.', static_folder='static')
app.config.from_object(Config)


# expose useful config values to templates
@app.context_processor
def inject_config():
    return {
        'GOOGLE_MAPS_API_KEY': app.config.get('GOOGLE_MAPS_API_KEY', ''),
        'RESTAURANT_ADDRESS': app.config.get('RESTAURANT_ADDRESS', '')
    }


def validate_google_maps_key():
    # Allow skipping validation via env var (set to 'false' to disable)
    validate_flag = os.environ.get('VALIDATE_GOOGLE_KEY', 'true').strip().lower()
    if validate_flag in ('0', 'false', 'no', 'n'):
        msg = 'Skipping Google Maps API key validation because VALIDATE_GOOGLE_KEY is set to false.'
        app.logger.info(msg)
        # persist skipped status
        try:
            var_dir = Path(app.root_path) / 'var'
            var_dir.mkdir(parents=True, exist_ok=True)
            out = {
                'checked': False,
                'validated': False,
                'status': 'SKIPPED',
                'message': msg,
                'checked_at': datetime.utcnow().isoformat() + 'Z'
            }
            (var_dir / 'google_maps_key_health.json').write_text(json.dumps(out))
        except Exception:
            pass
        return

    key = app.config.get('GOOGLE_MAPS_API_KEY', '')
    if not key:
        app.logger.warning('Environment variable GOOGLE_MAPS_API_KEY is not set. Google Maps features disabled.')
        return

    try:
        # lightweight request to Geocoding API to validate key
        query = urllib.parse.quote('Chh. Sambhajinagar')
        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={query}&key={key}'
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.load(resp)

        status = data.get('status', '')
        if status in ('OK', 'ZERO_RESULTS'):
            app.logger.info('GOOGLE_MAPS_API_KEY appears valid.')
            validated = True
            message = data.get('error_message', '') or 'Key valid'
        else:
            err = data.get('error_message', '')
            app.logger.warning(f'Google Maps API key validation returned status="{status}". {err}')
            validated = False
            message = err or f'status={status}'

        # persist validation result
        try:
            var_dir = Path(app.root_path) / 'var'
            var_dir.mkdir(parents=True, exist_ok=True)
            out = {
                'checked': True,
                'validated': bool(validated),
                'status': status,
                'message': message,
                'checked_at': datetime.utcnow().isoformat() + 'Z'
            }
            (var_dir / 'google_maps_key_health.json').write_text(json.dumps(out))
        except Exception:
            pass
    except Exception as e:
        app.logger.warning(f'Google Maps API key validation failed: {e}')
        try:
            var_dir = Path(app.root_path) / 'var'
            var_dir.mkdir(parents=True, exist_ok=True)
            out = {
                'checked': True,
                'validated': False,
                'status': 'ERROR',
                'message': str(e),
                'checked_at': datetime.utcnow().isoformat() + 'Z'
            }
            (var_dir / 'google_maps_key_health.json').write_text(json.dumps(out))
        except Exception:
            pass

DB.init_app(app)

with app.app_context():
    DB.create_all()
    # validate Google Maps API key at startup and log helpful messages
    validate_google_maps_key()

app.register_blueprint(auth_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(reservation_bp)
app.register_blueprint(admin_bp)


@app.route("/")
def home():
    return render_template("index.html", menu_sections=MENU_SECTIONS)

# Health endpoint to expose Google Maps API key validation result
@app.route('/health/maps')
def health_maps():
    # Optionally restrict to local/internal IPs
    bind_local = str(app.config.get('HEALTH_BIND_LOCAL', 'true')).strip().lower()
    trust_proxy = str(app.config.get('TRUST_PROXY', 'false')).strip().lower() in ('1','true','yes','y')

    def get_client_ip():
        # If behind a trusted proxy and X-Forwarded-For is present, use its first value
        if trust_proxy:
            xff = request.headers.get('X-Forwarded-For') or request.headers.get('x-forwarded-for')
            if xff:
                return xff.split(',')[0].strip()
        return request.remote_addr

    client_ip = get_client_ip() or ''
    allowlist_cfg = str(app.config.get('HEALTH_IP_ALLOWLIST', '') or '').strip()
    allowed_by_allowlist = False
    if allowlist_cfg:
        try:
            ip = ipaddress.ip_address(client_ip)
            for part in [p.strip() for p in allowlist_cfg.split(',') if p.strip()]:
                try:
                    net = ipaddress.ip_network(part, strict=False)
                    if ip in net:
                        allowed_by_allowlist = True
                        break
                except Exception:
                    continue
        except Exception:
            # unparsable client ip -> deny unless allowlist doesn't apply
            allowed_by_allowlist = False

    allowed_by_local = False
    if bind_local in ('1','true','yes','y'):
        try:
            ip = ipaddress.ip_address(client_ip)
            if ip.is_loopback or ip.is_private:
                allowed_by_local = True
        except Exception:
            allowed_by_local = False

    if not (allowed_by_allowlist or allowed_by_local):
        return Response('Forbidden', 403)

    # If security is configured, require a valid API key header or Basic auth
    health_key = app.config.get('HEALTH_API_KEY')
    basic_user = app.config.get('HEALTH_BASIC_USER')
    basic_pass = app.config.get('HEALTH_BASIC_PASS')

    def unauthorized():
        return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Health"'})

    if health_key or basic_user:
        authorized = False

        # API key via header or query
        if health_key:
            provided = request.headers.get('X-HEALTH-KEY') or request.args.get('key')
            if provided and provided == health_key:
                authorized = True

        # Basic auth
        if not authorized and basic_user:
            auth = request.authorization
            if auth and auth.username == basic_user and auth.password == basic_pass:
                authorized = True

        if not authorized:
            return unauthorized()

    var_file = Path(app.root_path) / 'var' / 'google_maps_key_health.json'
    if var_file.exists():
        try:
            data = json.loads(var_file.read_text())
            return jsonify(data)
        except Exception as e:
            return jsonify({
                'checked': True,
                'validated': False,
                'status': 'ERROR',
                'message': f'Failed to read health file: {e}'
            }), 500

    # fallback response when health file is absent
    key_present = bool(app.config.get('GOOGLE_MAPS_API_KEY'))
    return jsonify({
        'checked': False,
        'validated': False,
        'status': 'MISSING',
        'message': 'Health file not found',
        'google_maps_api_key_present': key_present
    })


if __name__ == "__main__":
    app.run(debug=True)