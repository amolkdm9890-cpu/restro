from pathlib import Path
import os


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'database.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    # Development admin credentials (change in production)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'amol')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '1234')

    # External API keys
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    # Health endpoint security
    HEALTH_API_KEY = os.environ.get('HEALTH_API_KEY', '')
    HEALTH_BASIC_USER = os.environ.get('HEALTH_BASIC_USER', '')
    HEALTH_BASIC_PASS = os.environ.get('HEALTH_BASIC_PASS', '')
    # Bind health endpoint to internal interfaces only when true
    HEALTH_BIND_LOCAL = os.environ.get('HEALTH_BIND_LOCAL', 'true')
    # When true, respect X-Forwarded-For for client IP (useful behind a trusted proxy)
    TRUST_PROXY = os.environ.get('TRUST_PROXY', 'false')
    # Optional comma-separated CIDR list to allow specific remote IPs (e.g. '203.0.113.0/24,198.51.100.5/32')
    HEALTH_IP_ALLOWLIST = os.environ.get('HEALTH_IP_ALLOWLIST', '')

    # Restaurant details
    RESTAURANT_ADDRESS = os.environ.get(
        'RESTAURANT_ADDRESS',
        "Office no 06, Amrut Sai, Jai's Ekdant Apartment, Near Yasho Mangal Karyalay, Pannalal Nagar, New Usmanapura, Chhatrapati Sambhaji Nagar 431001"
    )
