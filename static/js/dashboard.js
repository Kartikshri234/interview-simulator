(function () {
    const root = document.querySelector('.dashboard-layout');
    if (!root) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function clamp(value, min, max) {
        return Math.min(max, Math.max(min, value));
    }

    function animateCounters() {
        const counters = root.querySelectorAll('.count-up');
        counters.forEach((counter) => {
            const target = Number.parseFloat(counter.dataset.value || '0');
            const decimals = Number.parseInt(counter.dataset.decimals || '0', 10);

            if (Number.isNaN(target)) return;
            if (reduceMotion) {
                counter.firstChild.textContent = target.toFixed(decimals);
                return;
            }

            const duration = 850;
            const startTime = performance.now();

            function tick(now) {
                const progress = clamp((now - startTime) / duration, 0, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = target * eased;
                counter.firstChild.textContent = current.toFixed(decimals);
                if (progress < 1) requestAnimationFrame(tick);
            }

            requestAnimationFrame(tick);
        });
    }

    function updateScoreRing() {
        const insight = root.querySelector('.dash-insight');
        const ring = root.querySelector('#score-ring');
        const valueNode = root.querySelector('#score-ring-value');
        if (!insight || !ring || !valueNode) return;

        const score = clamp(Number.parseFloat(insight.dataset.score || '0'), 0, 10);
        const deg = score * 36;

        ring.style.setProperty('--fill', `${deg}deg`);
        valueNode.textContent = score.toFixed(1);
    }

    function updateMomentum() {
        const panel = root.querySelector('.dash-hero-panel');
        const fill = root.querySelector('#session-momentum-fill');
        if (!panel || !fill) return;

        const total = Number.parseInt(panel.dataset.total || '0', 10);
        const completed = Number.parseInt(panel.dataset.completed || '0', 10);
        const ratio = total > 0 ? clamp((completed / total) * 100, 0, 100) : 0;

        fill.style.width = `${ratio}%`;
    }

    function initFilters() {
        const filters = root.querySelectorAll('.chip-filter');
        const cards = root.querySelectorAll('.recent-item');
        const emptyState = root.querySelector('#recent-filter-empty');

        if (!filters.length || !cards.length) return;

        filters.forEach((button) => {
            button.addEventListener('click', () => {
                const selected = button.dataset.filter;
                let visibleCount = 0;

                filters.forEach((btn) => btn.classList.remove('is-active'));
                button.classList.add('is-active');

                cards.forEach((card) => {
                    const matches = selected === 'all' || card.dataset.status === selected;
                    card.classList.toggle('is-hidden', !matches);
                    if (matches) visibleCount += 1;
                });

                if (emptyState) emptyState.hidden = visibleCount !== 0;
            });
        });
    }

    animateCounters();
    updateScoreRing();
    updateMomentum();
    initFilters();

    /* ──────────────────────────────────────────────────
       Feature 4 — Progress Charts by Topic
       Two charts via Chart.js (loaded from CDN):
       1. Line chart: score trend over last 10 sessions
       2. Horizontal bar chart: avg score per category
       Tab switcher toggles between chart panels.
    ────────────────────────────────────────────────── */
    function initCharts() {
        const section = document.getElementById('dash-charts');
        if (!section) return;

        let chartData;
        try { chartData = JSON.parse(section.dataset.chart || '{}'); } catch { return; }

        const trend  = chartData.trend  || { labels: [], scores: [] };
        const topics = chartData.topics || { labels: [], scores: [], counts: [] };

        // Detect CSS variable colours for Chart.js
        const style   = getComputedStyle(document.documentElement);
        const primary = style.getPropertyValue('--primary').trim() || '#4f46e5';
        const text2   = style.getPropertyValue('--text-2').trim()  || '#475569';
        const border  = style.getPropertyValue('--border').trim()  || '#e2e8f0';
        const surface = style.getPropertyValue('--surface').trim() || '#ffffff';

        // Shared Chart.js defaults
        const baseFont = { family: 'Inter, system-ui, sans-serif', size: 12 };
        const gridColor = 'rgba(148,163,184,0.15)';

        /* ── Tab switcher ── */
        const tabs = section.querySelectorAll('.chart-tab');
        const panels = {
            trend:  document.getElementById('chart-panel-trend'),
            topics: document.getElementById('chart-panel-topics'),
        };
        tabs.forEach(function(tab) {
            tab.addEventListener('click', function() {
                tabs.forEach(function(t) { t.classList.remove('is-active'); });
                tab.classList.add('is-active');
                Object.keys(panels).forEach(function(key) {
                    panels[key].hidden = key !== tab.dataset.chartTab;
                });
            });
        });

        /* ── Load Chart.js then draw ── */
        if (window.Chart) {
            drawCharts();
        } else {
            var script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
            script.onload = drawCharts;
            document.head.appendChild(script);
        }

        function drawCharts() {
            /* ── 1. Score trend line chart ── */
            const trendEmpty = document.getElementById('chart-trend-empty');
            const trendWrap  = document.getElementById('chart-trend-wrap');
            if (!trend.scores.length) {
                if (trendEmpty) trendEmpty.hidden = false;
                if (trendWrap)  trendWrap.hidden  = true;
            } else {
                new window.Chart(document.getElementById('chart-trend'), {
                    type: 'line',
                    data: {
                        labels: trend.labels,
                        datasets: [{
                            label: 'Score',
                            data: trend.scores,
                            borderColor: primary,
                            backgroundColor: primary + '18',
                            borderWidth: 2.5,
                            pointBackgroundColor: primary,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            fill: true,
                            tension: 0.35,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: surface,
                                titleColor: primary,
                                bodyColor: text2,
                                borderColor: border,
                                borderWidth: 1,
                                padding: 10,
                                callbacks: {
                                    label: function(ctx) { return ' Score: ' + ctx.parsed.y + ' / 10'; },
                                },
                            },
                        },
                        scales: {
                            x: {
                                grid: { color: gridColor },
                                ticks: { color: text2, font: baseFont },
                                border: { color: border },
                            },
                            y: {
                                min: 0, max: 10,
                                grid: { color: gridColor },
                                ticks: { color: text2, font: baseFont, stepSize: 2 },
                                border: { color: border },
                            },
                        },
                    },
                });
            }

            /* ── 2. Category bar chart ── */
            const topicsEmpty = document.getElementById('chart-topics-empty');
            const topicsWrap  = document.getElementById('chart-topics-wrap');
            if (!topics.scores.length) {
                if (topicsEmpty) topicsEmpty.hidden = false;
                if (topicsWrap)  topicsWrap.hidden  = true;
            } else {
                // Colour each bar by score: green >= 7, amber 5-7, red < 5
                const barColors = topics.scores.map(function(s) {
                    return s >= 7 ? '#10b981' : (s >= 5 ? '#f59e0b' : '#ef4444');
                });
                new window.Chart(document.getElementById('chart-topics'), {
                    type: 'bar',
                    data: {
                        labels: topics.labels,
                        datasets: [{
                            label: 'Avg score',
                            data: topics.scores,
                            backgroundColor: barColors.map(function(c) { return c + 'cc'; }),
                            borderColor: barColors,
                            borderWidth: 1.5,
                            borderRadius: 6,
                        }],
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: surface,
                                titleColor: text2,
                                bodyColor: primary,
                                borderColor: border,
                                borderWidth: 1,
                                padding: 10,
                                callbacks: {
                                    label: function(ctx) {
                                        const i = ctx.dataIndex;
                                        return ' ' + ctx.parsed.x + '/10  (' + (topics.counts[i] || 0) + ' sessions)';
                                    },
                                },
                            },
                        },
                        scales: {
                            x: {
                                min: 0, max: 10,
                                grid: { color: gridColor },
                                ticks: { color: text2, font: baseFont, stepSize: 2 },
                                border: { color: border },
                            },
                            y: {
                                grid: { display: false },
                                ticks: { color: text2, font: baseFont },
                                border: { color: 'transparent' },
                            },
                        },
                    },
                });
            }
        }
    }

    initCharts();
})();
