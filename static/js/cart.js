const cart = JSON.parse(sessionStorage.getItem('cart') || '[]')

function getAuthenticatedUser() {
    const rawUser = localStorage.getItem('foodExpressUser')
    if (!rawUser) return null

    try {
        return JSON.parse(rawUser)
    } catch (error) {
        return null
    }
}

function addToCart(name, price) {
    if (!getAuthenticatedUser()) {
        const shouldLogin = confirm('Please login to buy products. Select OK for Login or Cancel for Register.')
        window.location.href = shouldLogin ? '/login' : '/register'
        return
    }

    cart.push({
        name,
        price
    })

    sessionStorage.setItem('cart', JSON.stringify(cart))

    alert(name + ' added to cart')
}

function loadCart() {
    const container = document.getElementById('cartItems')

    if (!container) return

    let total = 0

    container.innerHTML = ''

    cart.forEach(item => {
        total += Number(item.price) || 0

        container.innerHTML += `
        <div class="cart-item">
            <h2>${item.name}</h2>
            <p>₹${item.price}</p>
        </div>
        `
    })

    const totalElement = document.getElementById('total')
    if (totalElement) {
        totalElement.innerText = total
    }
}

function bindAddToCartButtons() {
    document.querySelectorAll('[data-add-to-cart]').forEach(button => {
        button.addEventListener('click', () => {
            addToCart(button.dataset.name, Number(button.dataset.price))
        })
    })
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        bindAddToCartButtons()
        loadCart()
    })
} else {
    bindAddToCartButtons()
    loadCart()
}

loadCart()
