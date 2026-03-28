/* =============================================================
   common.js  —  Shared utilities + JWT Auth Manager
   =============================================================
   JWT Auth Manager
   • Stores access + refresh tokens in localStorage
   • Decodes JWT payload to read expiry (exp claim)
   • Auto-refreshes access token before it expires
   • On hard failure → auto logout
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

    let animOff = false;
    try {
        animOff = localStorage.getItem('ui-animations') === 'false';
    } catch (_) {
        animOff = false;
    }
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
        try {
            if (access)  localStorage.setItem(KEYS.access,  access);
            if (refresh) localStorage.setItem(KEYS.refresh, refresh);
            if (user)    localStorage.setItem(KEYS.user, JSON.stringify(user));
        } catch(e) { console.warn('Auth: could not save tokens', e); }
    }

    function clearTokens() {
        try {
            localStorage.removeItem(KEYS.access);
            localStorage.removeItem(KEYS.refresh);
            localStorage.removeItem(KEYS.user);
        } catch(e) {}
    }

    function getAccess()  {
        try { return localStorage.getItem(KEYS.access); } catch { return null; }
    }
    function getRefresh() {
        try { return localStorage.getItem(KEYS.refresh); } catch { return null; }
    }
    function getUser()    {
        try { return JSON.parse(localStorage.getItem(KEYS.user) || 'null'); }
        catch { return null; }
    }

    function decodePayload(token) {
        try {
            const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
            // Pad base64 string correctly
            const padded = base64 + '=='.slice(0, (4 - base64.length % 4) % 4);
            return JSON.parse(atob(padded));
        } catch { return null; }
    }

    function isExpired(token, bufferSeconds = 0) {
        if (!token) return true;
        const payload = decodePayload(token);
        if (!payload || !payload.exp) return true;
        return payload.exp - Math.floor(Date.now() / 1000) < bufferSeconds;
    }

    let _refreshPromise = null;

    async function refreshAccessToken() {
        if (_refreshPromise) return _refreshPromise;
        _refreshPromise = (async () => {
            const refresh = getRefresh();
            if (!refresh || isExpired(refresh)) {
                forceLogout();
                throw new Error('Session expired.');
            }
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
        // If no token at all — try to obtain one silently via cookie session
        if (!access) {
            throw new Error('Not authenticated. Please log in.');
        }
        if (isExpired(access, REFRESH_BUFFER_SECONDS)) {
            access = await refreshAccessToken();
        }
        return access;
    }

    async function apiCall(url, options = {}) {
        let access;
        try {
            access = await getValidAccessToken();
        } catch(e) {
            forceLogout();
            throw e;
        }

        // Don't override Content-Type if caller passes FormData
        const isFormData = options.body instanceof FormData;
        const headers = Object.assign(
            isFormData ? {} : { 'Content-Type': 'application/json' },
            { 'Authorization': `Bearer ${access}`, 'X-CSRFToken': getCsrfToken() },
            options.headers || {}
        );

        const res = await fetch(url, Object.assign({}, options, { headers, credentials: 'same-origin' }));

        if (res.status === 401) {
            let newAccess;
            try { newAccess = await refreshAccessToken(); } catch { forceLogout(); throw new Error('Session expired.'); }
            const retryHeaders = Object.assign({}, headers, { 'Authorization': `Bearer ${newAccess}` });
            const retryRes = await fetch(url, Object.assign({}, options, { headers: retryHeaders, credentials: 'same-origin' }));
            if (retryRes.status === 401) { forceLogout(); throw new Error('Session expired.'); }
            return retryRes;
        }
        return res;
    }

    /**
     * Login: POST to JWT endpoint, store tokens, return response data.
     */
    async function login(identifier, password) {
        const res = await fetch('/api/auth/token/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: identifier, password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            const msg = data.detail
                || (data.email    && (Array.isArray(data.email)    ? data.email[0]    : data.email))
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
            try {
                await apiCall('/api/users/logout/', {
                    method: 'POST',
                    body: JSON.stringify({ refresh }),
                });
            } catch { /* best effort */ }
        }
        clearTokens();
        window.location.href = '/login/';
    }

    function forceLogout() {
        clearTokens();
        const authPages = ['/login/', '/register/'];
        if (!authPages.some(p => window.location.pathname.startsWith(p))) {
            window.location.href = '/login/?reason=expired';
        }
    }

    function isAuthenticated() {
        const access  = getAccess();
        const refresh = getRefresh();
        if (!access && !refresh) return false;
        // Consider authenticated if refresh token is still valid
        if (refresh && !isExpired(refresh)) return true;
        // Fall back to access token
        if (access  && !isExpired(access))  return true;
        return false;
    }

    function startAutoRefresh() {
        const access = getAccess();
        if (!access) return;
        const payload = decodePayload(access);
        if (!payload || !payload.exp) return;
        const refreshInMs = Math.max(
            (payload.exp - Math.floor(Date.now() / 1000) - REFRESH_BUFFER_SECONDS) * 1000,
            5000   // minimum 5 seconds
        );
        setTimeout(async function autoRefreshTick() {
            if (!isAuthenticated()) return;
            try { await refreshAccessToken(); startAutoRefresh(); }
            catch { /* forceLogout is called inside refreshAccessToken */ }
        }, refreshInMs);
    }

    // Boot: start auto-refresh only if we have tokens
    if (getAccess() || getRefresh()) {
        if (isAuthenticated()) startAutoRefresh();
    }

    return {
        login, logout, forceLogout,
        isAuthenticated, getUser, getAccess, getRefresh,
        apiCall, saveTokens, clearTokens, decodePayload,
    };
})();
