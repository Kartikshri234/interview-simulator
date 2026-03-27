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


/* ── Shared reveal animation ───────────────────────────── */
(function () {
    const items = document.querySelectorAll('.reveal');
    if (!items.length) return;

    const animOff      = localStorage.getItem('ui-animations') === 'false';
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reduceMotion || animOff || !('IntersectionObserver' in window)) {
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
    }, { threshold: 0.1 });

    items.forEach((item) => observer.observe(item));
})();


/* ── JWT Auth Manager ────────────────────────────────────── */
window.Auth = (function () {

    const KEYS = {
        access:  'jwt_access',
        refresh: 'jwt_refresh',
        user:    'jwt_user',
    };

    const REFRESH_BUFFER_SECONDS = 60;

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

    function decodePayload(token) {
        try {
            const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
            return JSON.parse(atob(base64));
        } catch { return null; }
    }

    function isExpired(token, bufferSeconds = 0) {
        const payload = decodePayload(token);
        if (!payload || !payload.exp) return true;
        return payload.exp - Math.floor(Date.now() / 1000) < bufferSeconds;
    }

    let _refreshPromise = null;

    async function refreshAccessToken() {
        if (_refreshPromise) return _refreshPromise;
        _refreshPromise = (async () => {
            const refresh = getRefresh();
            if (!refresh || isExpired(refresh)) { forceLogout(); throw new Error('Session expired.'); }
            const res = await fetch('/api/auth/token/refresh/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh }),
            });
            if (!res.ok) { forceLogout(); throw new Error('Session expired.'); }
            const data = await res.json();
            saveTokens(data.access, data.refresh || refresh, getUser());
            return data.access;
        })();
        _refreshPromise.finally(() => { _refreshPromise = null; });
        return _refreshPromise;
    }

    async function getValidAccessToken() {
        let access = getAccess();
        if (!access) { forceLogout(); throw new Error('Not authenticated.'); }
        if (isExpired(access, REFRESH_BUFFER_SECONDS)) access = await refreshAccessToken();
        return access;
    }

    async function apiCall(url, options = {}) {
        const access = await getValidAccessToken();
        const headers = Object.assign({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access}`,
            'X-CSRFToken': getCsrfToken(),
        }, options.headers || {});
        const res = await fetch(url, Object.assign({}, options, { headers, credentials: 'same-origin' }));
        if (res.status === 401) {
            let newAccess;
            try { newAccess = await refreshAccessToken(); } catch { forceLogout(); throw new Error('Session expired.'); }
            const retryRes = await fetch(url, Object.assign({}, options, {
                headers: Object.assign({}, headers, { 'Authorization': `Bearer ${newAccess}` }),
                credentials: 'same-origin',
            }));
            if (retryRes.status === 401) { forceLogout(); throw new Error('Session expired.'); }
            return retryRes;
        }
        return res;
    }

    /**
     * Login with username OR email.
     * Sends the identifier as the 'email' field — the backend resolver
     * handles both usernames and email addresses transparently.
     */
    async function login(identifier, password) {
        const res = await fetch('/api/auth/token/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // Always send as 'email'; backend resolves username → email internally
            body: JSON.stringify({ email: identifier, password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            // Surface the most useful error message
            const msg = data.detail
                || (data.email && data.email[0])
                || (data.non_field_errors && data.non_field_errors[0])
                || 'Invalid username/email or password.';
            throw new Error(msg);
        }

        const data = await res.json();
        saveTokens(data.access, data.refresh, data.user || null);
        return data;
    }

    async function logout() {
        const refresh = getRefresh();
        if (refresh) {
            try { await apiCall('/api/users/logout/', { method: 'POST', body: JSON.stringify({ refresh }) }); }
            catch { /* best effort */ }
        }
        clearTokens();
        window.location.href = '/login/';
    }

    function forceLogout() {
        clearTokens();
        const authPages = ['/login/', '/register/'];
        if (!authPages.includes(window.location.pathname)) window.location.href = '/login/?reason=expired';
    }

    function isAuthenticated() {
        const access = getAccess(), refresh = getRefresh();
        if (!access || !refresh) return false;
        return !isExpired(refresh);
    }

    function startAutoRefresh() {
        const access = getAccess();
        if (!access) return;
        const payload = decodePayload(access);
        if (!payload || !payload.exp) return;
        const refreshInMs = Math.max((payload.exp - Math.floor(Date.now() / 1000) - REFRESH_BUFFER_SECONDS) * 1000, 0);
        setTimeout(async function autoRefreshTick() {
            if (!isAuthenticated()) return;
            try { await refreshAccessToken(); startAutoRefresh(); } catch { forceLogout(); }
        }, refreshInMs);
    }

    if (getAccess() && isAuthenticated()) startAutoRefresh();

    return { login, logout, forceLogout, isAuthenticated, getUser, getAccess, apiCall, saveTokens, clearTokens };
})();
