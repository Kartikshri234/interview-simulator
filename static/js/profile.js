/* =============================================================
   profile.js  —  Profile page interactions
   - Avatar drag-and-drop upload with live preview
   - Password strength meter + match check
   - Toggle password reveal
   - Password section expand/collapse
   - JWT live inspector (reads from Auth module)
   - JWT copy token + manual refresh
   - Count-up on hero stats
   - Delete account confirm flow
   ============================================================= */
(function () {
    'use strict';

    /* ── 1. Count-up on hero stats ─────────────── */
    document.querySelectorAll('.count-up').forEach(function(el) {
        const target   = parseFloat(el.dataset.value   || '0');
        const decimals = parseInt(el.dataset.decimals  || '0', 10);
        if (isNaN(target)) return;
        const reduceMotion = window.matchMedia('(prefers-reduced-motion:reduce)').matches;

        let textNode = null;
        for (let i = 0; i < el.childNodes.length; i++) {
            if (el.childNodes[i].nodeType === Node.TEXT_NODE) { textNode = el.childNodes[i]; break; }
        }
        if (!textNode) { textNode = document.createTextNode(''); el.insertBefore(textNode, el.firstChild); }

        if (reduceMotion) { textNode.textContent = target.toFixed(decimals); return; }

        const start = performance.now();
        const dur   = 900;
        function tick(now) {
            const t = Math.min((now - start) / dur, 1);
            const e = 1 - Math.pow(1 - t, 3);
            textNode.textContent = (target * e).toFixed(decimals);
            if (t < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });

    /* ── 2. Avatar drag-and-drop ────────────────── */
    (function initAvatar() {
        const zone        = document.getElementById('avatar-drop-zone');
        const input       = document.getElementById('avatar-input');
        const previewWrap = document.getElementById('avatar-preview-wrap');
        const previewImg  = document.getElementById('avatar-preview-img');
        const placeholder = document.getElementById('avatar-placeholder-zone');
        const clearBtn    = document.getElementById('avatar-clear-btn');
        const phAvatar    = document.getElementById('ph-avatar-img');
        if (!zone || !input || !previewWrap || !previewImg || !placeholder || !clearBtn) return;

        function showPreview(file) {
            if (!file || !file.type.startsWith('image/')) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                previewWrap.style.display = 'block';
                placeholder.style.display = 'none';
                // Also update hero avatar live
                if (phAvatar && phAvatar.tagName === 'IMG') phAvatar.src = e.target.result;
                if (phAvatar && phAvatar.tagName !== 'IMG') phAvatar.style.backgroundImage = 'url(' + e.target.result + ')';
            };
            reader.readAsDataURL(file);
        }

        function clearPreview() {
            previewWrap.style.display = 'none';
            placeholder.style.display = 'flex';
            previewImg.src = '';
            input.value = '';
        }

        input.addEventListener('change', function() {
            if (input.files && input.files[0]) showPreview(input.files[0]);
        });
        clearBtn.addEventListener('click', function(e) { e.stopPropagation(); clearPreview(); });

        zone.addEventListener('dragover', function(e) { e.preventDefault(); zone.classList.add('drag-over'); });
        zone.addEventListener('dragleave', function() { zone.classList.remove('drag-over'); });
        zone.addEventListener('drop', function(e) {
            e.preventDefault();
            zone.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (!file) return;
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            showPreview(file);
        });
    })();

    /* ── 3. Password section toggle ─────────────── */
    (function initPasswordToggle() {
        const btn     = document.getElementById('pw-toggle-btn');
        const wrap    = document.getElementById('pw-form-wrap');
        const chevron = document.getElementById('pw-toggle-chevron');
        if (!btn || !wrap) return;

        btn.addEventListener('click', function() {
            const isOpen = wrap.style.display !== 'none';
            wrap.style.display = isOpen ? 'none' : 'block';
            btn.setAttribute('aria-expanded', !isOpen);
            if (chevron) chevron.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
        });
    })();

    /* ── 4. Password reveal buttons ─────────────── */
    document.querySelectorAll('.pw-reveal-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const field = document.getElementById(btn.dataset.target);
            if (!field) return;
            field.type = field.type === 'password' ? 'text' : 'password';
            btn.style.color = field.type === 'text' ? 'var(--primary)' : 'var(--text-3)';
        });
    });

    /* ── 5. Password strength meter ──────────────── */
    (function initPasswordStrength() {
        const newPw  = document.getElementById('new_password');
        const confPw = document.getElementById('confirm_password');
        const fill   = document.getElementById('pw-strength-fill');
        const label  = document.getElementById('pw-strength-label');
        const matchMsg = document.getElementById('pw-match-msg');
        if (!newPw || !fill || !label) return;

        function getStrength(pw) {
            let score = 0;
            if (pw.length >= 8)  score++;
            if (pw.length >= 12) score++;
            if (/[A-Z]/.test(pw)) score++;
            if (/[0-9]/.test(pw)) score++;
            if (/[^A-Za-z0-9]/.test(pw)) score++;
            return score;
        }

        const tiers = [
            { min: 0, label: 'Too short',  pct:  5, bg: 'var(--danger)' },
            { min: 1, label: 'Weak',       pct: 25, bg: 'var(--danger)' },
            { min: 2, label: 'Fair',       pct: 50, bg: 'var(--warning)' },
            { min: 3, label: 'Good',       pct: 70, bg: 'var(--warning)' },
            { min: 4, label: 'Strong',     pct: 88, bg: 'var(--success)' },
            { min: 5, label: 'Very strong',pct:100, bg: 'var(--success)' },
        ];

        function update() {
            const pw    = newPw.value;
            const score = getStrength(pw);
            const tier  = tiers[Math.min(score, tiers.length - 1)];
            fill.style.width      = (pw.length ? tier.pct : 0) + '%';
            fill.style.background = tier.bg;
            label.textContent     = pw.length ? tier.label : 'Enter a password';
            label.style.color     = pw.length ? tier.bg : 'var(--text-3)';
            checkMatch();
        }

        function checkMatch() {
            if (!confPw || !matchMsg) return;
            const a = newPw.value, b = confPw.value;
            if (!b) { matchMsg.hidden = true; return; }
            matchMsg.hidden = false;
            if (a === b) {
                matchMsg.textContent = '✓ Passwords match';
                matchMsg.style.color = 'var(--success)';
            } else {
                matchMsg.textContent = '✗ Passwords do not match';
                matchMsg.style.color = 'var(--danger)';
            }
        }

        newPw.addEventListener('input', update);
        if (confPw) confPw.addEventListener('input', checkMatch);
    })();

    /* ── 6. JWT live inspector ───────────────────── */
    (function initJwtInspector() {
        const Auth = window.Auth;
        if (!Auth) return;

        const dotEl      = document.getElementById('jwt-status-dot');
        const labelEl    = document.getElementById('jwt-status-label');
        const usernameEl = document.getElementById('jwt-username');
        const emailEl    = document.getElementById('jwt-email');
        const roleEl     = document.getElementById('jwt-role');
        const expLvlEl   = document.getElementById('jwt-exp-level');
        const staffEl    = document.getElementById('jwt-is-staff');
        const expiresEl  = document.getElementById('jwt-expires');
        const remainEl   = document.getElementById('jwt-remaining');
        const barEl      = document.getElementById('jwt-expiry-bar');
        const copyBtn    = document.getElementById('jwt-copy-btn');
        const refreshBtn = document.getElementById('jwt-manual-refresh');
        const logoutBtn  = document.getElementById('jwt-logout-all-btn');
        const toggleBtn  = document.getElementById('jwt-toggle-btn');
        const jwtBody    = document.getElementById('jwt-body');

        // Toggle panel
        if (toggleBtn && jwtBody) {
            toggleBtn.addEventListener('click', function() {
                const open = jwtBody.style.display !== 'none';
                jwtBody.style.display = open ? 'none' : 'block';
                toggleBtn.setAttribute('aria-expanded', !open);
                const sv = toggleBtn.querySelector('svg');
                if (sv) sv.style.transform = open ? 'rotate(0deg)' : 'rotate(180deg)';
            });
        }

        function setText(el, val) { if (el) el.textContent = val || '—'; }

        function formatDate(unixSec) {
            if (!unixSec) return '—';
            return new Date(unixSec * 1000).toLocaleString();
        }

        function formatRemaining(seconds) {
            if (seconds <= 0) return 'Expired';
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return m > 0 ? m + 'm ' + s + 's' : s + 's';
        }

        let tokenLifespan = null;

        function renderInspector() {
            const access  = Auth.getAccess();
            const user    = Auth.getUser();

            if (!access) {
                if (dotEl)   dotEl.className   = 'jwt-status-indicator invalid';
                if (labelEl) labelEl.textContent = 'No token — please log in';
                return;
            }

            const payload = Auth.decodePayload(access);
            if (!payload) {
                if (dotEl)   dotEl.className   = 'jwt-status-indicator invalid';
                if (labelEl) labelEl.textContent = 'Invalid token format';
                return;
            }

            const now       = Math.floor(Date.now() / 1000);
            const remaining = payload.exp ? payload.exp - now : 0;

            // On first render, capture lifespan
            if (tokenLifespan === null && payload.iat) {
                tokenLifespan = payload.exp - payload.iat;
            }

            // Status
            if (remaining <= 0) {
                if (dotEl)   dotEl.className   = 'jwt-status-indicator invalid';
                if (labelEl) labelEl.textContent = 'Token expired';
            } else if (remaining < 120) {
                if (dotEl)   dotEl.className   = 'jwt-status-indicator expiring';
                if (labelEl) labelEl.textContent = 'Token expiring soon';
            } else {
                if (dotEl)   dotEl.className   = 'jwt-status-indicator valid';
                if (labelEl) labelEl.textContent = 'Token valid';
            }

            // Fields from payload or user object
            const u = user || {};
            setText(usernameEl, payload.username || u.username);
            setText(emailEl,    payload.email    || u.email);
            setText(roleEl,     payload.is_staff ? '🛡 Staff' : '👤 User');
            setText(expLvlEl,   payload.experience_level || u.experience_level || '—');
            setText(staffEl,    payload.is_staff ? 'Yes' : 'No');
            setText(expiresEl,  formatDate(payload.exp));
            setText(remainEl,   formatRemaining(remaining));

            // Expiry bar
            if (barEl && tokenLifespan) {
                const pct = Math.max(0, Math.min(100, (remaining / tokenLifespan) * 100));
                barEl.style.width = pct + '%';
                barEl.style.background = remaining < 120
                    ? 'linear-gradient(90deg,var(--warning),var(--amber))'
                    : remaining < 300
                        ? 'linear-gradient(90deg,var(--primary),var(--mint))'
                        : 'linear-gradient(90deg,var(--success),var(--mint))';
            }
        }

        renderInspector();
        // Update every second
        setInterval(renderInspector, 1000);

        // Copy token
        if (copyBtn) {
            copyBtn.addEventListener('click', function() {
                const access = Auth.getAccess();
                if (!access) return;
                navigator.clipboard.writeText(access).then(function() {
                    const orig = copyBtn.textContent;
                    copyBtn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Copied!';
                    copyBtn.style.color = 'var(--success)';
                    setTimeout(function() {
                        copyBtn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy token';
                        copyBtn.style.color = '';
                    }, 2000);
                }).catch(function() {
                    copyBtn.textContent = 'Copy failed';
                });
            });
        }

        // Manual refresh
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                refreshBtn.disabled = true;
                refreshBtn.textContent = 'Refreshing…';
                Auth.apiCall('/api/users/me/', { method: 'GET' }).then(function() {
                    renderInspector();
                    refreshBtn.textContent = '✓ Refreshed';
                    setTimeout(function() {
                        refreshBtn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Refresh';
                        refreshBtn.disabled = false;
                    }, 2000);
                }).catch(function() {
                    refreshBtn.textContent = 'Failed';
                    refreshBtn.disabled = false;
                });
            });
        }

        // Sign out
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                if (!confirm('Sign out of all sessions?')) return;
                Auth.logout();
            });
        }
    })();

    /* ── 7. Profile form: unsaved changes warning ── */
    (function initFormDirty() {
        const form = document.getElementById('profile-form');
        if (!form) return;
        let dirty = false;
        form.addEventListener('change', function() { dirty = true; });
        window.addEventListener('beforeunload', function(e) {
            if (dirty) { e.preventDefault(); e.returnValue = ''; }
        });
        form.addEventListener('submit', function() { dirty = false; });
    })();

    /* ── 8. Delete account confirm flow ─────────── */
    (function initDeleteAccount() {
        const showBtn    = document.getElementById('delete-account-btn');
        const panel      = document.getElementById('delete-confirm-panel');
        const input      = document.getElementById('delete-confirm-input');
        const confirmBtn = document.getElementById('delete-confirm-btn');
        if (!showBtn || !panel || !input || !confirmBtn) return;

        showBtn.addEventListener('click', function() {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        });

        input.addEventListener('input', function() {
            const ok = input.value === 'DELETE';
            confirmBtn.disabled = !ok;
            confirmBtn.style.opacity = ok ? '1' : '.5';
            confirmBtn.style.cursor  = ok ? 'pointer' : 'default';
        });

        confirmBtn.addEventListener('click', function() {
            if (input.value !== 'DELETE') return;
            if (!confirm('This is permanent. Are you absolutely sure?')) return;
            // POST to delete endpoint — fallback to /profile/ if endpoint not available
            const auth = window.Auth;
            const req  = auth
                ? auth.apiCall('/api/users/delete-account/', { method: 'DELETE' })
                : fetch('/api/users/delete-account/', { method: 'DELETE', headers: { 'X-CSRFToken': window.getCsrfToken ? window.getCsrfToken() : '' } });
            req.then(function() {
                if (auth) auth.clearTokens();
                window.location.href = '/login/?deleted=1';
            }).catch(function() {
                alert('Could not delete account. Please contact support.');
            });
        });
    })();

})();
