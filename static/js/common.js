/* =============================================================
   common.js  —  Shared utilities + JWT Auth Manager
   =============================================================
   JWT Auth Manager
   ─────────────────
   • Stores access + refresh tokens in localStorage
   • Decodes JWT payload to read expiry (exp claim)
   • Auto-refreshes access token before it expires
   • On hard failure (refresh expired / blacklisted) → auto logout
   • apiCall() replaces plain fetch() for all authenticated requests
   ============================================================= */

/* ── CSRF helper ─────────────────────────────────────────── */
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


/* ── Theme toggle ────────────────────────────────────────── */
(function () {
    const ROOT    = document.documentElement;
    const BTN     = document.getElementById('theme-toggle');
    const STORAGE = 'ais-theme';
    const ICONS   = { dark: '🌙', light: '☀️' };

    function applyTheme(theme) {
        ROOT.setAttribute('data-theme', theme);
        if (BTN) BTN.textContent = ICONS[theme];
        localStorage.setItem(STORAGE, theme);
    }

    const saved  = localStorage.getItem(STORAGE);
    const system = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    applyTheme(saved || system);

    if (BTN) {
        BTN.addEventListener('click', function () {
            const current = ROOT.getAttribute('data-theme') || 'dark';
            applyTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
        if (!localStorage.getItem(STORAGE)) applyTheme(e.matches ? 'light' : 'dark');
    });
})();


/* ── Shared reveal animation ───────────────────────────── */
(function () {
    const items = document.querySelectorAll('.reveal');
    if (!items.length) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion || !('IntersectionObserver' in window)) {
        items.forEach((item) => item.classList.add('is-visible'));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    items.forEach((item) => observer.observe(item));
})();


/* ── JWT Auth Manager ────────────────────────────────────── */
window.Auth = (function () {

    const KEYS = {
        access:  'jwt_access',
        refresh: 'jwt_refresh',
        user:    'jwt_user',
    };

    // How many seconds BEFORE expiry we proactively refresh.
    const REFRESH_BUFFER_SECONDS = 60;

    /* ── Storage helpers ── */
    function saveTokens(access, refresh, user) {
        localStorage.setItem(KEYS.access,  access);
        localStorage.setItem(KEYS.refresh, refresh);
        if (user) localStorage.setItem(KEYS.user, JSON.stringify(user));
    }

    function clearTokens() {
        localStorage.removeItem(KEYS.access);
        localStorage.removeItem(KEYS.refresh);
        localStorage.removeItem(KEYS.user);
    }

    function getAccess()  { return localStorage.getItem(KEYS.access);  }
    function getRefresh() { return localStorage.getItem(KEYS.refresh); }
    function getUser()    {
        try { return JSON.parse(localStorage.getItem(KEYS.user) || 'null'); }
        catch { return null; }
    }

    /* ── JWT decode (no library needed — payload is just base64) ── */
    function decodePayload(token) {
        try {
            const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
            const json   = atob(base64);
            return JSON.parse(json);
        } catch {
            return null;
        }
    }

    /* ── Check if a token is expired (or will expire within buffer) ── */
    function isExpired(token, bufferSeconds = 0) {
        const payload = decodePayload(token);
        if (!payload || !payload.exp) return true;
        const nowSeconds = Math.floor(Date.now() / 1000);
        return payload.exp - nowSeconds < bufferSeconds;
    }

    /* ── Refresh the access token using the stored refresh token ── */
    let _refreshPromise = null; // deduplicate concurrent refresh calls

    async function refreshAccessToken() {
        // If a refresh is already in-flight, wait for it
        if (_refreshPromise) return _refreshPromise;

        _refreshPromise = (async () => {
            const refresh = getRefresh();
            if (!refresh || isExpired(refresh)) {
                // Refresh token itself is gone or expired → force logout
                forceLogout();
                throw new Error('Session expired. Please log in again.');
            }

            const res = await fetch('/api/auth/token/refresh/', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ refresh }),
            });

            if (!res.ok) {
                forceLogout();
                throw new Error('Session expired. Please log in again.');
            }

            const data = await res.json();
            // simplejwt returns: { access, refresh } (new refresh because ROTATE is True)
            saveTokens(data.access, data.refresh || refresh, getUser());
            return data.access;
        })();

        // Reset the shared promise after it settles
        _refreshPromise.finally(() => { _refreshPromise = null; });

        return _refreshPromise;
    }

    /* ── Get a valid access token, refreshing if needed ── */
    async function getValidAccessToken() {
        let access = getAccess();
        if (!access) {
            forceLogout();
            throw new Error('Not authenticated.');
        }
        // Proactively refresh if token expires within REFRESH_BUFFER_SECONDS
        if (isExpired(access, REFRESH_BUFFER_SECONDS)) {
            access = await refreshAccessToken();
        }
        return access;
    }

    /* ── Core authenticated fetch wrapper ── */
    async function apiCall(url, options = {}) {
        const access = await getValidAccessToken();

        const headers = Object.assign({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access}`,
            'X-CSRFToken':   getCsrfToken(),
        }, options.headers || {});

        const res = await fetch(url, Object.assign({}, options, {
            headers,
            credentials: 'same-origin',
        }));

        // 401 → try one more refresh then retry once
        if (res.status === 401) {
            let newAccess;
            try { newAccess = await refreshAccessToken(); }
            catch { forceLogout(); throw new Error('Session expired.'); }

            const retryHeaders = Object.assign({}, headers, {
                'Authorization': `Bearer ${newAccess}`,
            });
            const retryRes = await fetch(url, Object.assign({}, options, {
                headers: retryHeaders,
                credentials: 'same-origin',
            }));

            if (retryRes.status === 401) {
                forceLogout();
                throw new Error('Session expired. Please log in again.');
            }
            return retryRes;
        }

        return res;
    }

    /* ── Login: call the token endpoint, persist tokens ── */
    async function login(email, password) {
        const res = await fetch('/api/auth/token/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ email, password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'Invalid email or password.');
        }

        const data = await res.json();
        saveTokens(data.access, data.refresh, data.user || null);
        return data;
    }

    /* ── Logout: blacklist refresh token, clear storage, redirect ── */
    async function logout() {
        const refresh = getRefresh();
        if (refresh) {
            try {
                await apiCall('/api/users/logout/', {
                    method: 'POST',
                    body:   JSON.stringify({ refresh }),
                });
            } catch { /* best effort — clear locally regardless */ }
        }
        clearTokens();
        window.location.href = '/login/';
    }

    /* ── Force logout (no API call — used when tokens are dead) ── */
    function forceLogout() {
        clearTokens();
        // Only redirect if not already on an auth page
        const authPages = ['/login/', '/register/'];
        if (!authPages.includes(window.location.pathname)) {
            window.location.href = '/login/?reason=expired';
        }
    }

    /* ── Check if the user is currently authenticated ── */
    function isAuthenticated() {
        const access  = getAccess();
        const refresh = getRefresh();
        if (!access || !refresh) return false;
        // As long as refresh is still valid, user is considered authenticated
        return !isExpired(refresh);
    }

    /* ── Start a background timer to auto-refresh before expiry ── */
    function startAutoRefresh() {
        const access = getAccess();
        if (!access) return;
        const payload = decodePayload(access);
        if (!payload || !payload.exp) return;

        const nowSeconds     = Math.floor(Date.now() / 1000);
        const secondsLeft    = payload.exp - nowSeconds;
        const refreshInMs    = Math.max((secondsLeft - REFRESH_BUFFER_SECONDS) * 1000, 0);

        setTimeout(async function autoRefreshTick() {
            if (!isAuthenticated()) return;
            try {
                await refreshAccessToken();
                startAutoRefresh(); // reschedule after successful refresh
            } catch {
                forceLogout();
            }
        }, refreshInMs);
    }

    // Kick off auto-refresh when the page loads (if tokens exist)
    if (getAccess() && isAuthenticated()) {
        startAutoRefresh();
    }

    /* ── Expose public API ── */
    return {
        login,
        logout,
        forceLogout,
        isAuthenticated,
        getUser,
        getAccess,
        apiCall,
        saveTokens,
        clearTokens,
    };

})();
