/* =============================================================
   common.js  —  Shared utilities + JWT Auth Manager v2
   =============================================================
   JWT Auth Manager (window.Auth)
   ─────────────────────────────
   • Stores access + refresh tokens in localStorage
   • Decodes JWT payload without verification (for exp/claims)
   • Auto-refreshes access token BEFORE it expires (configurable buffer)
   • Deduplicates concurrent refresh calls via promise lock
   • Exponential back-off on refresh failure
   • On hard auth failure → forceLogout()
   • apiCall() — authenticated fetch with auto-retry on 401
   • login() / logout() helpers
   • getUser() — reads decoded claims from stored access token
   • tokenInfo() — returns full decoded payload
   • isTokenExpiring() — handy for proactive UI warnings
   ============================================================= */

/* ── CSRF helper ─────────────────────────────────────── */
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


/* ── Shared reveal animation ─────────────────────────── */
(function () {
    const items = document.querySelectorAll('.reveal');
    if (!items.length) return;

    let animOff = false;
    try { animOff = localStorage.getItem('ui-animations') === 'false'; } catch (_) {}
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reduceMotion || animOff || !('IntersectionObserver' in window)) {
        items.forEach(function(item) { item.classList.add('is-visible'); });
        return;
    }

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08 });

    items.forEach(function(item) { observer.observe(item); });
})();


/* ══════════════════════════════════════════════════════════
   JWT AUTH MANAGER
══════════════════════════════════════════════════════════ */
window.Auth = (function () {
    'use strict';

    // ── Storage keys ──────────────────────────────────
    const KEYS = {
        access:  'jwt_access',
        refresh: 'jwt_refresh',
        user:    'jwt_user',
    };

    // ── Config ────────────────────────────────────────
    const REFRESH_BUFFER_SEC   = 90;   // refresh if token expires within 90 s
    const MAX_RETRY_ATTEMPTS   = 3;
    const BASE_BACKOFF_MS      = 500;

    // ── Internal state ────────────────────────────────
    let _refreshPromise   = null;   // de-dup concurrent refresh calls
    let _retryCount       = 0;
    let _autoRefreshTimer = null;

    // ── Storage helpers ───────────────────────────────
    function save(key, val) {
        try { if (val != null) localStorage.setItem(key, val); } catch(e) { console.warn('Auth.save:', e); }
    }
    function load(key) {
        try { return localStorage.getItem(key); } catch { return null; }
    }
    function remove(key) {
        try { localStorage.removeItem(key); } catch {}
    }

    function saveTokens(access, refresh, user) {
        if (access)  save(KEYS.access,  access);
        if (refresh) save(KEYS.refresh, refresh);
        if (user)    save(KEYS.user, typeof user === 'string' ? user : JSON.stringify(user));
    }

    function clearTokens() {
        remove(KEYS.access);
        remove(KEYS.refresh);
        remove(KEYS.user);
    }

    function getAccess()  { return load(KEYS.access); }
    function getRefresh() { return load(KEYS.refresh); }
    function getStoredUser() {
        try { return JSON.parse(load(KEYS.user) || 'null'); } catch { return null; }
    }

    // ── JWT decode (no signature verification) ────────
    function decodePayload(token) {
        if (!token || typeof token !== 'string') return null;
        try {
            const parts = token.split('.');
            if (parts.length !== 3) return null;
            const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
            const padded = b64 + '=='.slice(0, (4 - b64.length % 4) % 4);
            return JSON.parse(atob(padded));
        } catch { return null; }
    }

    function getExp(token) {
        const p = decodePayload(token);
        return p && p.exp ? p.exp : null;
    }

    function isExpired(token, bufferSec) {
        bufferSec = bufferSec || 0;
        if (!token) return true;
        const exp = getExp(token);
        if (!exp) return true;
        return (exp - Math.floor(Date.now() / 1000)) < bufferSec;
    }

    function secondsUntilExpiry(token) {
        const exp = getExp(token);
        if (!exp) return 0;
        return Math.max(0, exp - Math.floor(Date.now() / 1000));
    }

    // ── Public: isTokenExpiring — useful for UI hints ──
    function isTokenExpiring(thresholdSec) {
        thresholdSec = thresholdSec || 120;
        const access = getAccess();
        if (!access) return true;
        return secondsUntilExpiry(access) < thresholdSec;
    }

    // ── Token info for inspector ───────────────────────
    function tokenInfo() {
        const access  = getAccess();
        const refresh = getRefresh();
        return {
            accessPayload:       decodePayload(access),
            refreshPayload:      decodePayload(refresh),
            accessSecondsLeft:   secondsUntilExpiry(access),
            refreshSecondsLeft:  secondsUntilExpiry(refresh),
            isAccessExpired:     isExpired(access),
            isRefreshExpired:    isExpired(refresh),
        };
    }

    // ── Refresh access token ──────────────────────────
    async function refreshAccessToken() {
        // De-dup: return the same promise if already refreshing
        if (_refreshPromise) return _refreshPromise;

        _refreshPromise = (async function() {
            const refresh = getRefresh();

            if (!refresh || isExpired(refresh)) {
                forceLogout();
                throw new Error('Session expired. Please log in again.');
            }

            let backoffMs = BASE_BACKOFF_MS;

            for (let attempt = 1; attempt <= MAX_RETRY_ATTEMPTS; attempt++) {
                try {
                    const res = await fetch('/api/auth/token/refresh/', {
                        method:  'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body:    JSON.stringify({ refresh }),
                    });

                    if (res.ok) {
                        const data = await res.json();
                        saveTokens(data.access, data.refresh || refresh, getStoredUser());
                        _retryCount = 0;
                        return data.access;
                    }

                    // 401 / 400 → token invalid; don't retry
                    if (res.status === 401 || res.status === 400) {
                        forceLogout();
                        throw new Error('Session expired.');
                    }

                    // 5xx → transient; back off and retry
                    if (attempt < MAX_RETRY_ATTEMPTS) {
                        await new Promise(function(r) { setTimeout(r, backoffMs); });
                        backoffMs *= 2;
                    }
                } catch (err) {
                    if (attempt >= MAX_RETRY_ATTEMPTS) throw err;
                    await new Promise(function(r) { setTimeout(r, backoffMs); });
                    backoffMs *= 2;
                }
            }

            forceLogout();
            throw new Error('Unable to refresh session. Please log in again.');
        })();

        _refreshPromise.finally(function() { _refreshPromise = null; });
        return _refreshPromise;
    }

    // ── Get a valid access token (refresh if needed) ──
    async function getValidAccessToken() {
        let access = getAccess();
        if (!access) throw new Error('Not authenticated. Please log in.');
        if (isExpired(access, REFRESH_BUFFER_SEC)) {
            access = await refreshAccessToken();
        }
        return access;
    }

    // ── Authenticated fetch ───────────────────────────
    async function apiCall(url, options) {
        options = options || {};

        let access;
        try {
            access = await getValidAccessToken();
        } catch(e) {
            forceLogout();
            throw e;
        }

        const isFormData = options.body instanceof FormData;
        const headers = Object.assign(
            isFormData ? {} : { 'Content-Type': 'application/json' },
            {
                'Authorization': 'Bearer ' + access,
                'X-CSRFToken':   getCsrfToken(),
            },
            options.headers || {}
        );

        const finalOptions = Object.assign({}, options, { headers: headers, credentials: 'same-origin' });
        let res;

        try {
            res = await fetch(url, finalOptions);
        } catch (networkErr) {
            throw new Error('Network error: ' + networkErr.message);
        }

        // 401 → try one silent refresh and retry
        if (res.status === 401) {
            let newAccess;
            try {
                newAccess = await refreshAccessToken();
            } catch {
                forceLogout();
                throw new Error('Session expired. Please log in again.');
            }

            const retryHeaders = Object.assign({}, headers, { 'Authorization': 'Bearer ' + newAccess });
            const retryOptions = Object.assign({}, finalOptions, { headers: retryHeaders });
            res = await fetch(url, retryOptions);

            if (res.status === 401) {
                forceLogout();
                throw new Error('Session expired. Please log in again.');
            }
        }

        return res;
    }

    // ── Login ─────────────────────────────────────────
    async function login(identifier, password) {
        const res = await fetch('/api/auth/token/', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ email: identifier, password: password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(function() { return {}; });
            const msg  =  data.detail
                       || (data.email          && (Array.isArray(data.email)          ? data.email[0]          : data.email))
                       || (data.non_field_errors && data.non_field_errors[0])
                       || 'Invalid credentials. Please try again.';
            throw new Error(msg);
        }

        const data = await res.json();

        // Use user object from response body, or decode from token
        const user = data.user || decodePayload(data.access) || null;
        saveTokens(data.access, data.refresh, user);
        startAutoRefresh();
        return data;
    }

    // ── Logout ────────────────────────────────────────
    async function logout() {
        const refresh = getRefresh();
        if (refresh) {
            try {
                await apiCall('/api/users/logout/', {
                    method: 'POST',
                    body:   JSON.stringify({ refresh: refresh }),
                });
            } catch { /* best effort — clear tokens regardless */ }
        }
        clearTokens();
        stopAutoRefresh();
        window.location.href = '/login/';
    }

    // ── Force logout (non-interactive) ───────────────
    function forceLogout() {
        clearTokens();
        stopAutoRefresh();
        const authPaths = ['/login/', '/register/'];
        const here      = window.location.pathname;
        if (!authPaths.some(function(p) { return here.startsWith(p); })) {
            window.location.href = '/login/?reason=expired';
        }
    }

    // ── Auth check ────────────────────────────────────
    function isAuthenticated() {
        const refresh = getRefresh();
        if (refresh && !isExpired(refresh)) return true;
        const access = getAccess();
        return !!(access && !isExpired(access));
    }

    // ── getUser — prefers payload from access token ───
    function getUser() {
        const access = getAccess();
        if (access) {
            const payload = decodePayload(access);
            if (payload && payload.username) return payload;
        }
        return getStoredUser();
    }

    // ── Auto-refresh scheduler ────────────────────────
    function stopAutoRefresh() {
        if (_autoRefreshTimer) { clearTimeout(_autoRefreshTimer); _autoRefreshTimer = null; }
    }

    function startAutoRefresh() {
        stopAutoRefresh();
        const access = getAccess();
        if (!access) return;
        const payload = decodePayload(access);
        if (!payload || !payload.exp) return;

        const secsLeft  = payload.exp - Math.floor(Date.now() / 1000);
        const refreshIn = Math.max((secsLeft - REFRESH_BUFFER_SEC) * 1000, 5000);

        _autoRefreshTimer = setTimeout(async function tick() {
            if (!isAuthenticated()) return;
            try {
                await refreshAccessToken();
                startAutoRefresh();
            } catch { /* forceLogout already called inside */ }
        }, refreshIn);
    }

    // Boot
    if (isAuthenticated()) startAutoRefresh();

    // ── Public API ────────────────────────────────────
    return {
        // Auth flow
        login, logout, forceLogout,
        // State
        isAuthenticated, getUser, getAccess, getRefresh,
        // Token tools
        decodePayload, tokenInfo, isTokenExpiring,
        // Fetch
        apiCall,
        // Storage (for advanced use)
        saveTokens, clearTokens,
    };
})();
