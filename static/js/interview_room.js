(function () {
    const sessionId = window.INTERVIEW_SESSION_ID;
    if (!sessionId) return;

    const statusEl   = document.getElementById('room-status');
    const questionEl = document.getElementById('question-text');
    const startBtn   = document.getElementById('start-session-btn');
    const endBtn     = document.getElementById('end-session-btn');
    const answerForm = document.getElementById('answer-form');
    const answerText = document.getElementById('answer-text');

    function setStatus(text) { statusEl.textContent = text; }

    /* ──────────────────────────────────────────────────
       Feature 1 — Visual Countdown Timer
       Uses time_limit_seconds from the API question payload.
       Ring stroke-dashoffset animates from 0 → 113 (full circle).
       Colours: primary → warning (<=40%) → danger (<=15%).
       Auto-submits the answer when the timer reaches zero.
    ────────────────────────────────────────────────── */
    const timerWrap     = document.getElementById('timer-bar-wrap');
    const timerDisplay  = document.getElementById('timer-display');
    const timerTitle    = document.getElementById('timer-bar-title');
    const timerRingFill = document.getElementById('timer-ring-fill');
    const timerProgress = document.getElementById('timer-progress-fill');
    const timerBadge    = document.getElementById('timer-status-badge');
    const RING_CIRC     = 113; // 2 * PI * r18 ≈ 113

    let _timerInterval  = null;
    let _timerTotal     = 0;
    let _timerRemaining = 0;

    function formatTime(sec) {
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return m > 0 ? m + ':' + String(s).padStart(2, '0') : s + 's';
    }

    function updateTimerUI(remaining, total) {
        if (!timerWrap || !timerDisplay || !timerRingFill || !timerProgress || !timerBadge) return;
        const pct  = total > 0 ? remaining / total : 1;
        const used = 1 - pct;

        timerDisplay.textContent  = formatTime(remaining);
        timerRingFill.style.strokeDashoffset = (used * RING_CIRC).toFixed(2);
        timerProgress.style.width = (pct * 100).toFixed(1) + '%';

        timerWrap.classList.remove('timer-warning', 'timer-danger');
        if (pct <= 0.15) {
            timerWrap.classList.add('timer-danger');
            timerBadge.textContent = 'Time critical';
        } else if (pct <= 0.40) {
            timerWrap.classList.add('timer-warning');
            timerBadge.textContent = 'Wrap up';
        } else {
            timerBadge.textContent = 'On track';
        }
    }

    function startTimer(seconds) {
        if (!timerWrap) return;
        stopTimer();
        _timerTotal     = seconds;
        _timerRemaining = seconds;

        timerWrap.hidden = false;
        timerTitle.textContent = 'Time remaining — ' + formatTime(seconds) + ' limit';
        updateTimerUI(seconds, seconds);

        _timerInterval = setInterval(function () {
            _timerRemaining -= 1;
            if (_timerRemaining <= 0) {
                _timerRemaining = 0;
                updateTimerUI(0, _timerTotal);
                stopTimer();
                timerBadge.textContent = 'Time\'s up';
                // Auto-submit whatever is typed
                if (answerText.value.trim()) {
                    answerForm.dispatchEvent(new Event('submit', { cancelable: true }));
                } else {
                    setStatus('Time\'s up. Move to the next question.');
                }
                return;
            }
            updateTimerUI(_timerRemaining, _timerTotal);
        }, 1000);
    }

    function stopTimer() {
        if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
    }

    /* ──────────────────────────────────────────────────
       Feature 2 — Ideal Answer Side Panel
       Shown after answer is submitted. Displays
       ideal_answer_outline + expected_keywords from
       the API response. Dismissed by close button
       or automatically on next question.
    ────────────────────────────────────────────────── */
    const idealPanel   = document.getElementById('ideal-panel');
    const idealBody    = document.getElementById('ideal-panel-body');
    const idealKws     = document.getElementById('ideal-keywords');
    const idealClose   = document.getElementById('ideal-panel-close');
    const idealToggle  = document.getElementById('ideal-toggle-btn');

    function showIdealPanel(outline, keywords) {
        idealBody.textContent = outline || 'No outline available for this question.';
        idealKws.innerHTML = '';
        if (keywords && keywords.length) {
            keywords.forEach(function(kw) {
                var chip = document.createElement('span');
                chip.className = 'ideal-kw';
                chip.textContent = kw;
                idealKws.appendChild(chip);
            });
        }
        idealPanel.hidden = false;
        idealToggle.hidden = true;
    }

    function hideIdealPanel() {
        idealPanel.hidden = true;
        idealToggle.hidden = true;
    }

    if (idealClose) idealClose.addEventListener('click', hideIdealPanel);
    if (idealToggle) idealToggle.addEventListener('click', function() {
        if (!idealPanel.hidden) { hideIdealPanel(); } else { idealPanel.hidden = false; if (idealToggle) idealToggle.textContent = 'Hide ideal answer'; }
    });

    /* ──────────────────────────────────────────────────
       Feature 5 — Question Text-to-Speech
       Uses the free Web Speech API (SpeechSynthesis).
       Button appears once a question loads.
       Click once → reads aloud. Click again → stops.
       Auto-stops when a new question is loaded.
    ────────────────────────────────────────────────── */
    const ttsBtn       = document.getElementById('tts-btn');
    const ttsBtnLabel  = document.getElementById('tts-btn-label');
    const ttsIconSpeak = document.getElementById('tts-icon-speak');
    const ttsIconStop  = document.getElementById('tts-icon-stop');
    const ttsSupported = ('speechSynthesis' in window);

    function ttsSetSpeaking(speaking) {
        ttsBtn.classList.toggle('tts-speaking', speaking);
        ttsIconSpeak.hidden = speaking;
        ttsIconStop.hidden  = !speaking;
        ttsBtnLabel.textContent = speaking ? 'Stop' : 'Read aloud';
    }

    function ttsStop() {
        if (ttsSupported) window.speechSynthesis.cancel();
        ttsSetSpeaking(false);
    }

    function ttsRead(text) {
        if (!ttsSupported || !text) return;
        ttsStop();
        const utter = new SpeechSynthesisUtterance(text);
        utter.rate  = 0.92;
        utter.pitch = 1;
        utter.onend = function() { ttsSetSpeaking(false); };
        utter.onerror = function() { ttsSetSpeaking(false); };
        window.speechSynthesis.speak(utter);
        ttsSetSpeaking(true);
    }

    if (ttsBtn && ttsSupported) {
        ttsBtn.addEventListener('click', function() {
            if (window.speechSynthesis.speaking) {
                ttsStop();
            } else {
                ttsRead(questionEl.textContent.trim());
            }
        });
    } else if (ttsBtn) {
        ttsBtn.hidden = true; // hide if browser doesn't support
    }

    // All fetch calls go through Auth.apiCall so the JWT access token
    // is attached automatically and silently refreshed when near expiry.

    async function startSession() {
        setStatus('Starting interview session...');
        startBtn.disabled = true;

        try {
            const res = await window.Auth.apiCall(
                '/api/interview/sessions/' + sessionId + '/start/',
                { method: 'POST' }
            );

            if (!res.ok) throw new Error('Failed to start session.');
            const data     = await res.json();
            const question = data.question || data.question_text || 'Session started. Waiting for question payload.';
            questionEl.textContent = question;
            setStatus('Session started. Submit your answer below.');
            if (ttsBtn && ttsSupported) ttsBtn.hidden = false; // Feature 5: show TTS button
            // Feature 1: start countdown using time_limit_seconds from payload
            const limit = data.time_limit_seconds || 120;
            startTimer(limit);
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
            const res = await window.Auth.apiCall(
                '/api/interview/sessions/' + sessionId + '/answer/',
                {
                    method: 'POST',
                    body:   JSON.stringify({ answer_text: text }),
                }
            );

            if (!res.ok) throw new Error('Answer submission failed.');
            const data = await res.json();

            if (data.next_question) {
                questionEl.textContent = data.next_question;
                answerText.value = '';
                setStatus('Answer recorded. Next question loaded.');
                ttsStop();         // Feature 5: stop any ongoing speech
                hideIdealPanel();  // Feature 2: clear ideal panel for new question
                // Feature 1: restart timer for next question
                const nextLimit = data.time_limit_seconds || 120;
                startTimer(nextLimit);
                return;
            }

            if (data.completed) {
                stopTimer(); // Feature 1: stop timer on completion
                setStatus('Interview completed. Redirecting to results...');
                window.location.href = window.INTERVIEW_RESULTS_URL;
                return;
            }

            // Feature 2: show ideal answer after submission
            if (data.ideal_answer_outline !== undefined || data.expected_keywords !== undefined) {
                showIdealPanel(data.ideal_answer_outline, data.expected_keywords);
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
            const res = await window.Auth.apiCall(
                '/api/interview/sessions/' + sessionId + '/end/',
                { method: 'POST' }
            );

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
