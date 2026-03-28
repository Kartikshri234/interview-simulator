(function () {
    const form = document.getElementById('new-interview-form');
    if (!form) return;

    const statusEl  = document.getElementById('new-interview-status');
    const submitBtn = document.getElementById('new-interview-submit');

    /* ──────────────────────────────────────────────────
       Feature 8 — Adaptive difficulty suggestion
    ────────────────────────────────────────────────── */
    const adaptiveHint  = document.getElementById('adaptive-hint');
    const adaptiveText  = document.getElementById('adaptive-hint-text');
    const adaptiveApply = document.getElementById('adaptive-apply');
    const diffSelect    = form.querySelector('select[name="difficulty"]');
    let   suggestedDiff = null;

    async function fetchAdaptive(category) {
        if (!adaptiveHint || !window.Auth) return;
        try {
            const res  = await window.Auth.apiCall(
                '/api/interview/adaptive-difficulty/?category=' + encodeURIComponent(category)
            );
            if (!res.ok) return;
            const data = await res.json();
            suggestedDiff = data.suggested_difficulty;
            if (adaptiveText) adaptiveText.textContent = data.reason || '';
            adaptiveHint.hidden = false;
        } catch(e) {
            // silently skip — not critical
        }
    }

    form.querySelectorAll('input[name="category"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            if (adaptiveHint) adaptiveHint.hidden = true;
            fetchAdaptive(radio.value);
        });
    });

    if (adaptiveApply) {
        adaptiveApply.addEventListener('click', function() {
            if (suggestedDiff && diffSelect) {
                diffSelect.value = suggestedDiff;
                adaptiveApply.textContent = 'Applied ✓';
                adaptiveApply.disabled = true;
                setTimeout(function() {
                    adaptiveApply.textContent = 'Apply suggestion';
                    adaptiveApply.disabled = false;
                }, 2000);
            }
        });
    }

    // Fetch adaptive hint on page load
    var checkedCat = form.querySelector('input[name="category"]:checked');
    if (checkedCat) fetchAdaptive(checkedCat.value);

    /* ── Form submit — create session via API ── */
    form.addEventListener('submit', async function (event) {
        event.preventDefault();

        // Check authentication
        if (!window.Auth) {
            statusEl.textContent = 'Auth system not loaded. Please refresh.';
            return;
        }

        submitBtn.disabled   = true;
        statusEl.textContent = 'Creating session…';

        const formData = new FormData(form);
        const payload  = {
            title:           (formData.get('title') || '').toString().trim(),
            category:        formData.get('category') || 'python',
            difficulty:      formData.get('difficulty') || 'medium',
            total_questions: parseInt(formData.get('total_questions') || '5', 10),
            session_type:    formData.get('session_type') || 'standard',
        };

        try {
            const response = await window.Auth.apiCall('/api/interview/sessions/', {
                method: 'POST',
                body:   JSON.stringify(payload),
            });

            if (!response.ok) {
                let reason = 'Unable to create session.';
                try {
                    const errData = await response.json();
                    reason = errData.detail || errData.error
                        || Object.values(errData).flat().join(' ')
                        || reason;
                } catch (_) {}
                throw new Error(reason);
            }

            const data = await response.json();
            const id   = data.id || data.pk;
            if (!id) throw new Error('Session created but ID is missing in response.');

            statusEl.textContent = 'Session created! Redirecting…';
            window.location.href = '/interview/' + id + '/';

        } catch (error) {
            statusEl.textContent = error.message || 'Something went wrong. Please try again.';
            submitBtn.disabled   = false;
        }
    });
})();
