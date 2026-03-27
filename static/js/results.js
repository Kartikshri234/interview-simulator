(function () {
    const page = document.querySelector('[data-page="results"]');
    if (!page) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function clamp(value, min, max) {
        return Math.min(max, Math.max(min, value));
    }

    /* ── Count-up animations ── */
    const counters = document.querySelectorAll('.count-up');
    counters.forEach((counter) => {
        const target = Number.parseFloat(counter.dataset.value || '0');
        const decimals = Number.parseInt(counter.dataset.decimals || '0', 10);

        if (Number.isNaN(target)) return;
        if (reduceMotion) {
            const firstTextNode = counter.childNodes[0];
            if (firstTextNode) firstTextNode.textContent = target.toFixed(decimals);
            return;
        }

        const duration = 850;
        const start = performance.now();

        function tick(now) {
            const progress = clamp((now - start) / duration, 0, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = target * eased;
            const firstTextNode = counter.childNodes[0];
            if (firstTextNode) firstTextNode.textContent = value.toFixed(decimals);
            if (progress < 1) requestAnimationFrame(tick);
        }

        requestAnimationFrame(tick);
    });

    /* ────────────────────────────────────────────────────────────
       Feature 14 — Facial Emotion Heatmap
       Reads avg emotion data injected by the Django view as
       window.EMOTION_DATA. Renders a radar chart via Chart.js.
    ──────────────────────────────────────────────────────────── */
    function initEmotionChart() {
        const data = window.EMOTION_DATA || {};
        const canvas = document.getElementById('emotion-chart');
        if (!canvas || !Object.keys(data).length) return;

        const labels = Object.keys(data);
        const values = Object.values(data);

        const style   = getComputedStyle(document.documentElement);
        const primary = style.getPropertyValue('--primary').trim() || '#4f46e5';
        const text2   = style.getPropertyValue('--text-2').trim()  || '#475569';

        function draw() {
            new window.Chart(canvas, {
                type: 'radar',
                data: {
                    labels: labels.map(function(l) { return l.charAt(0).toUpperCase() + l.slice(1); }),
                    datasets: [{
                        label: 'Avg %',
                        data: values,
                        borderColor: primary,
                        backgroundColor: primary + '22',
                        borderWidth: 2,
                        pointBackgroundColor: primary,
                        pointRadius: 4,
                    }],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) { return ' ' + ctx.parsed.r.toFixed(1) + '%'; },
                            },
                        },
                    },
                    scales: {
                        r: {
                            min: 0,
                            ticks: { stepSize: 20, color: text2, font: { size: 11 } },
                            pointLabels: { color: text2, font: { size: 12 } },
                            grid: { color: 'rgba(148,163,184,0.2)' },
                        },
                    },
                },
            });

            // Colour legend chips
            const legend = document.getElementById('emotion-legend');
            const EMOTION_COLOURS = {
                happy: '#10b981', neutral: '#6366f1', surprised: '#f59e0b',
                sad: '#3b82f6', angry: '#ef4444', disgusted: '#8b5cf6',
                fearful: '#f97316',
            };
            if (legend) {
                labels.forEach(function(lbl, i) {
                    const chip = document.createElement('span');
                    chip.style.cssText = 'display:inline-flex;align-items:center;gap:5px;font-size:12px;padding:3px 9px;border-radius:20px;background:' + (EMOTION_COLOURS[lbl] || '#64748b') + '22;color:' + (EMOTION_COLOURS[lbl] || '#64748b');
                    chip.textContent = lbl.charAt(0).toUpperCase() + lbl.slice(1) + ' ' + values[i].toFixed(1) + '%';
                    legend.appendChild(chip);
                });
            }
        }

        if (window.Chart) {
            draw();
        } else {
            var script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
            script.onload = draw;
            document.head.appendChild(script);
        }
    }

    initEmotionChart();

    /* ────────────────────────────────────────────────────────────
       Feature 7 — Bookmark questions from results page
       Each answer card has a .bookmark-btn with data-session and
       data-question. Clicking POSTs to the bookmark API.
    ──────────────────────────────────────────────────────────── */
    document.querySelectorAll('.bookmark-btn').forEach(function(btn) {
        btn.addEventListener('click', async function() {
            const sessionId    = btn.dataset.session;
            const questionText = btn.dataset.question;
            const path         = btn.querySelector('.bm-path');
            const label        = btn.querySelector('.bm-label');

            btn.disabled = true;
            try {
                const res = await window.Auth.apiCall(
                    '/api/interview/sessions/' + sessionId + '/bookmark/',
                    {
                        method: 'POST',
                        body: JSON.stringify({ question_text: questionText }),
                    }
                );
                const data = await res.json();
                if (res.ok) {
                    // Visual confirmation: fill the bookmark icon
                    if (path) path.setAttribute('fill', 'currentColor');
                    if (label) label.textContent = data.created ? 'Bookmarked ✓' : 'Already saved';
                    btn.style.color = 'var(--primary)';
                } else {
                    if (label) label.textContent = 'Error';
                    btn.disabled = false;
                }
            } catch (e) {
                if (label) label.textContent = 'Error';
                btn.disabled = false;
            }
        });
    });

})();
