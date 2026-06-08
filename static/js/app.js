document.addEventListener('DOMContentLoaded', function () {
    // Hero entrance
    var hero = document.querySelector('.hero');
    if (hero) {
        hero.classList.add('animate-hero');
        setTimeout(function () { hero.classList.add('delay'); }, 80);
    }

    // Stagger cards as they come into view
    var cards = document.querySelectorAll('.card');
    if ('IntersectionObserver' in window && cards.length) {
        var io = new IntersectionObserver(function (entries, obs) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var el = entry.target;
                    var idx = Array.prototype.indexOf.call(cards, el);
                    var delayType = idx % 3 === 0 ? 'small' : (idx % 3 === 1 ? 'med' : 'lg');
                    el.setAttribute('data-anim-delay', delayType);
                    el.classList.add('in-view');
                    obs.unobserve(el);
                }
            });
        }, { threshold: 0.12 });
        cards.forEach(function (c) { io.observe(c); });
    } else {
        // Fallback: reveal all cards
        cards.forEach(function (c) { c.classList.add('in-view'); });
    }

    // Button ripple for primary buttons (small, elegant)
    document.body.addEventListener('click', function (e) {
        var btn = e.target.closest('.btn-primary');
        if (!btn) return;
        var circle = document.createElement('span');
        circle.style.position = 'absolute';
        circle.style.width = circle.style.height = '8px';
        circle.style.borderRadius = '50%';
        circle.style.left = (e.offsetX - 4) + 'px';
        circle.style.top = (e.offsetY - 4) + 'px';
        circle.style.background = 'rgba(255,255,255,0.2)';
        circle.style.pointerEvents = 'none';
        circle.style.transform = 'scale(0)';
        circle.style.transition = 'transform 420ms cubic-bezier(.2,.9,.2,1), opacity 420ms ease';
        btn.style.position = 'relative';
        btn.appendChild(circle);
        requestAnimationFrame(function () {
            circle.style.transform = 'scale(18)';
            circle.style.opacity = '0';
        });
        setTimeout(function () { circle.remove(); }, 480);
    });
});
