// ── 토스트 알림 (Toast) ──────────────────────────────────────────
// [수정 2026-06-25] 모바일: 하단 중앙 / 데스크탑: 우하단 고정
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        // [이전 코드] 'fixed bottom-5 right-5 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none'
        container.className = 'fixed bottom-5 z-[100] flex flex-col gap-2 pointer-events-none left-4 right-4 md:left-auto md:right-5 md:w-80';
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

// ── 데모 모드 전역 플래그 및 차단 헬퍼 ─────────────────────────────
window._demoMode = false;

function blockIfDemo() {
    if (window._demoMode) {
        showToast('데모 계정은 조회만 가능합니다.', 'warning');
        return true;
    }
    return false;
}

// ── 데모 모드 배너 주입 ──────────────────────────────────────────────
function injectDemoBanner() {
    if (document.getElementById('demo-mode-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'demo-mode-banner';
    // fixed: 네비바(64px) 바로 아래에 고정, 어떤 레이아웃(flex/grid/block)이든 영향 없음
    banner.style.cssText = 'position:fixed;top:64px;left:0;right:0;z-index:49;box-sizing:border-box;';
    banner.className = 'bg-amber-50 border-b-2 border-amber-300 text-amber-800 px-4 py-3 text-center text-sm font-semibold w-full';
    banner.innerHTML = `
        <div class="max-w-screen-xl mx-auto flex items-center justify-center gap-2 flex-wrap">
            <span class="material-symbols-outlined text-[18px] shrink-0">experiment</span>
            <span>데모 버전으로 체험 중입니다. 저장·수정 등 일부 기능이 제한됩니다.</span>
            <a href="/login.html" class="ml-2 px-3 py-1 bg-primary text-white rounded-full text-xs hover:opacity-90 whitespace-nowrap font-semibold">지금 가입하면 모든 기능 무료!</a>
        </div>
    `;
    document.body.appendChild(banner);

    // 배너 높이만큼 <main>에 추가 패딩을 주어 콘텐츠가 배너에 가려지지 않게 함
    requestAnimationFrame(() => {
        const h = banner.getBoundingClientRect().height;
        const main = document.querySelector('main');
        if (main && h > 0) {
            const currentPt = parseFloat(getComputedStyle(main).paddingTop) || 0;
            main.style.paddingTop = (currentPt + h) + 'px';
        }
    });
}

// ── 데모 차단 모달 ──────────────────────────────────────────────────
function showDemoBlockModal() {
    let modal = document.getElementById('demo-block-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'demo-block-modal';
        modal.className = 'fixed inset-0 z-[200] flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" onclick="closeDemoBlockModal()"></div>
            <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm p-8 z-10 text-center">
                <span class="material-symbols-outlined text-5xl text-amber-500 mb-3 block">experiment</span>
                <h2 class="text-xl font-bold text-gray-900 mb-2">데모 모드 제한</h2>
                <p class="text-gray-600 text-sm mb-6">이 기능은 데모 버전에서 사용할 수 없습니다.<br>지금 가입하면 모든 기능을 무료로 이용하실 수 있어요!</p>
                <div class="flex gap-3">
                    <button onclick="closeDemoBlockModal()" class="flex-1 py-3 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50">계속 둘러보기</button>
                    <a href="/login.html" class="flex-1 py-3 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 flex items-center justify-center">무료 가입하기</a>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    modal.classList.remove('hidden');
}

function closeDemoBlockModal() {
    const modal = document.getElementById('demo-block-modal');
    if (modal) modal.classList.add('hidden');
}

// 데모 차단 응답(403 + status="blocked") 처리 헬퍼
// 사용법: const data = await r.json(); if (handleDemoBlock(data)) return;
function handleDemoBlock(data) {
    if (data && data.status === 'blocked') {
        showDemoBlockModal();
        return true;
    }
    return false;
}

// ── 네비게이션 및 공통 UI 초기화 ───────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
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
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath === currentPath) {
            link.classList.add('text-primary', 'font-bold');
            link.classList.remove('text-on-surface-variant');
        }
    });

    // ── 데모 모드 배너 자동 주입 ──────────────────────────────────
    // 보호 페이지에서만 실행 (login.html, main.html, admin.html 제외)
    const skipPages = ['login.html', 'main.html', 'admin.html', ''];
    if (!skipPages.includes(currentPath)) {
        try {
            const r = await fetch('/api/auth/me', { credentials: 'same-origin' });
            if (r.ok) {
                const data = await r.json();
                if (data.success && data.user && (data.user.email === 'demo@a4u.com' || data.mode === 'DEMO')) {
                    window._demoMode = true;
                    injectDemoBanner();
                }
            }
        } catch (_) {}
    }
});
