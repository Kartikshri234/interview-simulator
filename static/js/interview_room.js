(function () {
    const sessionId = window.INTERVIEW_SESSION_ID;
    if (!sessionId) return;

    const statusEl = document.getElementById('room-status');
    const questionEl = document.getElementById('question-text');
    const startBtn = document.getElementById('start-session-btn');
    const endBtn = document.getElementById('end-session-btn');
    const answerForm = document.getElementById('answer-form');
    const answerText = document.getElementById('answer-text');

    function setStatus(text) {
        statusEl.textContent = text;
    }

    async function startSession() {
        setStatus('Starting interview session...');
        startBtn.disabled = true;

        try {
            const res = await fetch('/api/interview/sessions/' + sessionId + '/start/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.getCsrfToken()
                },
                credentials: 'same-origin'
            });

            if (!res.ok) throw new Error('Failed to start session.');
            const data = await res.json();
            const question = data.question || data.question_text || 'Session started. Waiting for question payload.';
            questionEl.textContent = question;
            setStatus('Session started. Submit your answer below.');
        } catch (error) {
            setStatus(error.message || 'Could not start session.');
            startBtn.disabled = false;
        }
    }

    async function submitAnswer(event) {
        event.preventDefault();
        const text = answerText.value.trim();
        if (!text) return;

        setStatus('Submitting answer...');
        try {
            const res = await fetch('/api/interview/sessions/' + sessionId + '/answer/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                body: JSON.stringify({ answer_text: text }),
                credentials: 'same-origin'
            });

            if (!res.ok) throw new Error('Answer submission failed.');
            const data = await res.json();

            if (data.next_question) {
                questionEl.textContent = data.next_question;
                answerText.value = '';
                setStatus('Answer recorded. Next question loaded.');
                return;
            }

            if (data.completed) {
                setStatus('Interview completed. Redirecting to results...');
                window.location.href = window.INTERVIEW_RESULTS_URL;
                return;
            }

            setStatus('Answer saved.');
        } catch (error) {
            setStatus(error.message || 'Could not submit answer.');
        }
    }

    async function endSession() {
        setStatus('Ending session...');
        endBtn.disabled = true;

        try {
            const res = await fetch('/api/interview/sessions/' + sessionId + '/end/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.getCsrfToken()
                },
                credentials: 'same-origin'
            });

            if (!res.ok) throw new Error('Could not end session.');
            window.location.href = window.INTERVIEW_RESULTS_URL;
        } catch (error) {
            setStatus(error.message || 'Failed to end session.');
            endBtn.disabled = false;
        }
    }

    startBtn.addEventListener('click', startSession);
    answerForm.addEventListener('submit', submitAnswer);
    endBtn.addEventListener('click', endSession);
})();
