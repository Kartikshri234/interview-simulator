(function () {
    const form      = document.getElementById('new-interview-form');
    if (!form) return;

    const statusEl  = document.getElementById('new-interview-status');
    const submitBtn = document.getElementById('new-interview-submit');

    /* ──────────────────────────────────────────────────
       Feature 8 — Adaptive difficulty suggestion
       When a category radio is selected, fetch the
       suggested difficulty from the API and show a
       hint badge the user can apply with one click.
    ────────────────────────────────────────────────── */
    const adaptiveHint  = document.getElementById('adaptive-hint');
    const adaptiveText  = document.getElementById('adaptive-hint-text');
    const adaptiveApply = document.getElementById('adaptive-apply');
    const diffSelect    = form.querySelector('select[name="difficulty"]');
    let   suggestedDiff = null;

    async function fetchAdaptive(category) {
        if (!window.Auth || !window.Auth.isAuthenticated()) return;
        if (!adaptiveHint) return;
        try {
            const res  = await window.Auth.apiCall('/api/interview/adaptive-difficulty/?category=' + encodeURIComponent(category));
            if (!res.ok) return;
            const data = await res.json();
            suggestedDiff = data.suggested_difficulty;
            if (adaptiveText) adaptiveText.textContent = data.reason || '';
            adaptiveHint.hidden = false;
        } catch { /* silently skip */ }
    }

    // Listen for category radio changes
    form.querySelectorAll('input[name="category"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            if (adaptiveHint) adaptiveHint.hidden = true;
            fetchAdaptive(radio.value);
        });
    });

    // Apply suggestion button
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

    // Fetch on page load for the already-checked category
    var checkedCat = form.querySelector('input[name="category"]:checked');
    if (checkedCat) fetchAdaptive(checkedCat.value);

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        submitBtn.disabled  = true;
        statusEl.textContent = 'Creating session...';

        const formData = new FormData(form);
        const payload  = {
            title:           (formData.get('title') || '').toString().trim(),
            category:        formData.get('category') || 'python',
            difficulty:      formData.get('difficulty') || 'medium',
            total_questions: Number(formData.get('total_questions') || 5),
            session_type:    formData.get('session_type') || 'standard',  // Feature 13
        };

        try {
            const response = await window.Auth.apiCall('/api/interview/sessions/', {
                method: 'POST',
                body:   JSON.stringify(payload),
            });

            if (!response.ok) {
                const data   = await response.json().catch(() => ({}));
                const reason = data.detail || data.error || 'Unable to create session.';
                throw new Error(reason);
            }

            const data = await response.json();
            const id   = data.id || data.pk;
            if (!id) throw new Error('Session created but id is missing in response.');

            statusEl.textContent = 'Session created. Redirecting...';
            window.location.href = '/interview/' + id + '/';

        } catch (error) {
            statusEl.textContent = error.message || 'Something went wrong while creating session.';
            submitBtn.disabled   = false;
        }
    });
})();
