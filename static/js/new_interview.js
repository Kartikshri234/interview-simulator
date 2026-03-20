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
            category:        formData.get('category'),
            difficulty:      formData.get('difficulty'),
            total_questions: Number(formData.get('total_questions') || 5),
        };

        try {
            // Use Auth.apiCall so the JWT access token is sent automatically,
            // and the token is silently refreshed if it's about to expire.
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
