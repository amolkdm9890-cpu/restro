async function login() {
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  if (!email || !password) {
    alert('Please enter email and password');
    return;
  }

  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      alert(data.message || 'Login failed');
      return;
    }

    // Save any client-side state if needed and redirect
    if (data.user) {
      try { localStorage.setItem('foodExpressUser', JSON.stringify(data.user)) } catch (e) { /* ignore */ }
    }
    if (data.redirect) window.location.href = data.redirect;
    else window.location.reload();
  } catch (err) {
    console.error(err);
    alert('Network error while logging in');
  }
}

async function register() {
  const username = document.getElementById('username').value.trim();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const phone = document.getElementById('phone').value.trim();
  const address = document.getElementById('address').value.trim();

  if (!username || !email || !password) {
    alert('Please fill username, email and password');
    return;
  }

  try {
    const res = await fetch('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, phone, address })
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      alert(data.message || 'Registration failed');
      return;
    }
    if (data.user) {
      try { localStorage.setItem('foodExpressUser', JSON.stringify(data.user)) } catch (e) { /* ignore */ }
    }
    if (data.redirect) window.location.href = data.redirect;
    else window.location.reload();
  } catch (err) {
    console.error(err);
    alert('Network error while registering');
  }
}
