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

// ── 데모 모드 배너 주입 ──────────────────────────────────────────────
function injectDemoBanner() {
    if (document.getElementById('demo-mode-banner')) return;
    var banner = document.createElement('div');
    banner.id = 'demo-mode-banner';
    banner.style.cssText = 'background:#fffbeb;border-bottom:2px solid #fcd34d;color:#92400e;padding:10px 16px;text-align:center;font-size:14px;font-weight:600;width:100%;';
    banner.innerHTML =
        '<div style="max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap;">' +
        '<span class="material-symbols-outlined" style="font-size:18px;flex-shrink:0;">experiment</span>' +
        '<span>데모 버전으로 체험 중입니다. 저장·수정 등 일부 기능이 제한됩니다.</span>' +
        '<a href="/login.html" style="margin-left:8px;padding:2px 12px;background:#3525cd;color:#fff;border-radius:999px;font-size:12px;text-decoration:none;white-space:nowrap;font-weight:700;">지금 가입하면 모든 기능 무료!</a>' +
        '</div>';
    var main = document.querySelector('main');
    if (main) {
        main.insertBefore(banner, main.firstChild);
    } else {
        document.body.insertBefore(banner, document.body.firstChild);
    }
}

// ── 데모 차단 모달 ──────────────────────────────────────────────────
function showDemoBlockModal() {
    var modal = document.getElementById('demo-block-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'demo-block-modal';
        modal.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px;';
        modal.innerHTML =
            '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.4);" onclick="closeDemoBlockModal()"></div>' +
            '<div style="position:relative;background:#fff;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.3);width:100%;max-width:360px;padding:32px;z-index:10;text-align:center;">' +
            '<span class="material-symbols-outlined" style="font-size:48px;color:#f59e0b;display:block;margin-bottom:12px;">experiment</span>' +
            '<h2 style="font-size:20px;font-weight:700;color:#111827;margin-bottom:8px;">데모 모드 제한</h2>' +
            '<p style="font-size:14px;color:#6b7280;margin-bottom:24px;line-height:1.6;">이 기능은 데모 버전에서 사용할 수 없습니다.<br>지금 가입하면 모든 기능을 무료로 이용하실 수 있어요!</p>' +
            '<div style="display:flex;gap:12px;">' +
            '<button onclick="closeDemoBlockModal()" style="flex:1;padding:12px;border:1px solid #e5e7eb;border-radius:12px;font-size:14px;font-weight:500;color:#6b7280;cursor:pointer;background:#fff;">계속 둘러보기</button>' +
            '<a href="/login.html" style="flex:1;padding:12px;background:#2563eb;color:#fff;border-radius:12px;font-size:14px;font-weight:700;text-decoration:none;display:flex;align-items:center;justify-content:center;">무료 가입하기</a>' +
            '</div>' +
            '</div>';
        document.body.appendChild(modal);
    }
    modal.style.display = 'flex';
}

function closeDemoBlockModal() {
    var modal = document.getElementById('demo-block-modal');
    if (modal) modal.style.display = 'none';
}

// 데모 차단 응답(403 + status="blocked") 처리 헬퍼
function handleDemoBlock(data) {
    if (data && data.status === 'blocked') {
        showDemoBlockModal();
        return true;
    }
    return false;
}

document.addEventListener('DOMContentLoaded', function () {
    var mobileMenuButton = document.getElementById('mobile-menu-button');
    var mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenu.classList.remove('hidden');

        var menuIcon = mobileMenuButton.querySelector('.material-symbols-outlined');

        function openMenu() {
            mobileMenu.classList.add('open');
            mobileMenuButton.classList.add('open');
            if (menuIcon) menuIcon.textContent = 'close';
        }

        function closeMenu() {
            mobileMenu.classList.remove('open');
            mobileMenuButton.classList.remove('open');
            if (menuIcon) menuIcon.textContent = 'menu';
        }

        mobileMenuButton.addEventListener('click', function (e) {
            e.stopPropagation();
            mobileMenu.classList.contains('open') ? closeMenu() : openMenu();
        });

        document.addEventListener('click', function (e) {
            if (mobileMenu.classList.contains('open') &&
                !mobileMenu.contains(e.target) &&
                !mobileMenuButton.contains(e.target)) {
                closeMenu();
            }
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

    // ── 데모 모드 배너 자동 주입 ──────────────────────────────────
    var skipPages = ['login.html', 'main.html', 'admin.html', ''];
    if (skipPages.indexOf(currentPath) === -1) {
        fetch('/api/auth/me', { credentials: 'same-origin' })
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) {
                if (data && data.success && data.user && data.user.email === 'demo@a4u.com') {
                    injectDemoBanner();
                }
            })
            .catch(function() {});
    }
});
