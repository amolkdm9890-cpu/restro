function setAuthenticatedUser(user) {
    localStorage.setItem('foodExpressUser', JSON.stringify(user))
}

function getAuthenticatedUser() {
    const rawUser = localStorage.getItem('foodExpressUser')
    if (!rawUser) return null

    try {
        return JSON.parse(rawUser)
    } catch (error) {
        return null
    }
}

async function register() {
    const username = document.getElementById('username').value.trim()
    const email = document.getElementById('email').value.trim()
    const password = document.getElementById('password').value
    const phone = document.getElementById('phone')?.value.trim() || ''
    const address = document.getElementById('address')?.value.trim() || ''

    const response = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username,
            email,
            password,
            phone,
            address
        })
    })

    const data = await response.json()

    alert(data.message)

    if (response.ok && data.user) {
        setAuthenticatedUser(data.user)
    }

    if (response.ok && data.redirect) {
        window.location.href = data.redirect
    }
}

async function login() {
    const email = document.getElementById('loginEmail').value.trim()
    const password = document.getElementById('loginPassword').value

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            email,
            password
        })
    })

    const data = await response.json()

    alert(data.message)

    if (response.ok && data.user) {
        setAuthenticatedUser(data.user)
    }

    if (response.ok && data.redirect) {
        window.location.href = data.redirect
    }
}