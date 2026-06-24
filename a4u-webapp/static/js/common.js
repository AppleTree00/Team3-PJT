function showToast(message, type) {
    var t = type || 'info';
    var container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
        document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    toast.style.cssText = 'padding:14px 18px;border-radius:12px;color:#fff;font-size:14px;font-weight:500;box-shadow:0 4px 16px rgba(0,0,0,0.18);display:flex;align-items:center;gap:10px;transition:all 0.3s;transform:translateY(8px);opacity:0;pointer-events:auto;max-width:320px;';
    var colors = { success: '#059669', error: '#dc2626', warning: '#d97706', info: '#1e293b' };
    var icons  = { success: 'check_circle', error: 'error', warning: 'warning', info: 'info' };
    toast.style.backgroundColor = colors[t] || colors.info;
    toast.innerHTML =
        '<span class="material-symbols-outlined" style="font-size:18px;">' + (icons[t] || icons.info) + '</span>' +
        '<span>' + message + '</span>';
    container.appendChild(toast);
    requestAnimationFrame(function () {
        requestAnimationFrame(function () {
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';
        });
    });
    setTimeout(function () {
        toast.style.transform = 'translateY(8px)';
        toast.style.opacity = '0';
        setTimeout(function () { toast.remove(); }, 300);
    }, 3500);
}

function handleUnavailableFeature() {
    showToast('준비 중인 기능입니다. 데모 버전에서는 지원하지 않습니다.', 'warning');
}

document.addEventListener('DOMContentLoaded', function () {
    var mobileMenuButton = document.getElementById('mobile-menu-button');
    var mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            mobileMenu.classList.toggle('hidden');
        });
    }

    var currentPath = window.location.pathname.split('/').pop() || 'main.html';
    var navLinks = document.querySelectorAll('.nav-link');
    var mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    function setActiveLink(links) {
        links.forEach(function (link) {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('text-primary', 'font-bold');
                link.classList.remove('text-on-surface-variant');
            }
        });
    }
    setActiveLink(navLinks);
    setActiveLink(mobileNavLinks);
});
