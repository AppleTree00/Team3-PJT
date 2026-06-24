// ── 토스트 알림 (Toast) ──────────────────────────────────────────
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-5 right-5 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `p-4 rounded-xl shadow-lg text-white font-medium text-sm transition-all duration-300 transform translate-y-2 opacity-0 pointer-events-auto flex items-center gap-3`;
    
    const colors = {
        success: 'bg-emerald-600',
        error: 'bg-rose-600',
        warning: 'bg-amber-500',
        info: 'bg-slate-800'
    };
    toast.classList.add(colors[type] || colors.info);

    const icons = {
        success: 'check_circle',
        error: 'error',
        warning: 'warning',
        info: 'info'
    };
    
    toast.innerHTML = `
        <span class="material-symbols-outlined text-[20px] shrink-0">${icons[type] || icons.info}</span>
        <span class="flex-1">${message}</span>
    `;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    setTimeout(() => {
        toast.classList.add('translate-y-2', 'opacity-0');
        toast.addEventListener('transitionend', () => {
            toast.remove();
            if (container.children.length === 0) {
                container.remove();
            }
        });
    }, 3000);
}

// ── 미구현 기능 안내 팝업 ──────────────────────────────────────────
function handleUnavailableFeature() {
    showToast('준비 중인 기능입니다. 데모 버전에서는 지원하지 않습니다.', 'warning');
}

// ── 네비게이션 및 공통 UI 초기화 ───────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Set active navigation link
    const currentPath = window.location.pathname.split('/').pop() || 'main.html';
    const navLinks = document.querySelectorAll('.nav-link');
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');

    const setActiveLink = (links) => {
        links.forEach(link => {
            const linkPath = link.getAttribute('href');
            if (linkPath === currentPath) {
                link.classList.add('text-primary', 'font-bold');
                link.classList.remove('text-on-surface-variant');
            }
        });
    };

    setActiveLink(navLinks);
    setActiveLink(mobileNavLinks);
});