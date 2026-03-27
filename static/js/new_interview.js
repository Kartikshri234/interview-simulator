(function () {
    const form      = document.getElementById('new-interview-form');
    if (!form) return;

    const statusEl  = document.getElementById('new-interview-status');
    const submitBtn = document.getElementById('new-interview-submit');

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
