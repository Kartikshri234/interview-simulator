/* ── CSRF helper ── */
window.getCsrfToken = function () {
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith('csrftoken=')) {
            return decodeURIComponent(trimmed.slice('csrftoken='.length));
        }
    }
    return '';
};

/* ── Theme toggle ── */
(function () {
    const ROOT    = document.documentElement;
    const BTN     = document.getElementById('theme-toggle');
    const STORAGE = 'ais-theme';

    const ICONS = { dark: '🌙', light: '☀️' };

    function applyTheme(theme) {
        ROOT.setAttribute('data-theme', theme);
        if (BTN) BTN.textContent = ICONS[theme];
        localStorage.setItem(STORAGE, theme);
    }

    // On load: respect saved preference, then system preference, then default dark
    const saved  = localStorage.getItem(STORAGE);
    const system = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    applyTheme(saved || system);

    if (BTN) {
        BTN.addEventListener('click', function () {
            const current = ROOT.getAttribute('data-theme') || 'dark';
            applyTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    // Keep in sync if user changes OS preference while page is open
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
        if (!localStorage.getItem(STORAGE)) {
            applyTheme(e.matches ? 'light' : 'dark');
        }
    });
})();
