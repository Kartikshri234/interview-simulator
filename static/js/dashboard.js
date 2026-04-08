/* =============================================================
   dashboard.js  —  Interactive dashboard logic
   - Time-based greeting
   - Count-up animations
   - Momentum ring + bar
   - Score ring + readiness badge
   - Tier highlights
   - Recent sessions: live search + status filter
   - Chart.js charts (trend + by topic)
   ============================================================= */
(function () {
    'use strict';

    const root = document.getElementById('dashboard-root');
    if (!root) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ── Helpers ─────────────────────────────── */
    function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
    function lerp(a, b, t)    { return a + (b - a) * t; }
    function easeOut(t)       { return 1 - Math.pow(1 - t, 3); }

    function animateValue(from, to, durationMs, decimals, onTick, onDone) {
        if (reduceMotion) { onTick(to); if (onDone) onDone(); return; }
        const start = performance.now();
        function tick(now) {
            const t = clamp((now - start) / durationMs, 0, 1);
            onTick(parseFloat((lerp(from, to, easeOut(t))).toFixed(decimals)));
            if (t < 1) requestAnimationFrame(tick);
            else if (onDone) onDone();
        }
        requestAnimationFrame(tick);
    }

    /* ── 1. Greeting ─────────────────────────── */
    (function initGreeting() {
        const el = document.getElementById('greeting-text');
        if (!el) return;
        const h = new Date().getHours();
        el.textContent = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
    })();

    /* ── 2. Count-up KPI values ──────────────── */
    (function initCounters() {
        root.querySelectorAll('.count-up').forEach(function(el) {
            const target   = parseFloat(el.dataset.value || '0');
            const decimals = parseInt(el.dataset.decimals || '0', 10);
            if (isNaN(target)) return;

            // Preserve inner <span> (e.g. "/10", "d") by using a dedicated text node
            let textNode = null;
            for (let i = 0; i < el.childNodes.length; i++) {
                if (el.childNodes[i].nodeType === Node.TEXT_NODE) { textNode = el.childNodes[i]; break; }
            }
            if (!textNode) { textNode = document.createTextNode(''); el.insertBefore(textNode, el.firstChild); }

            animateValue(0, target, 900, decimals, function(v) {
                textNode.textContent = v.toFixed(decimals);
            });
        });
    })();

    /* ── 3. Momentum ring + bar ───────────────── */
    (function initMomentum() {
        const fill    = document.getElementById('mp-bar-fill');
        const ring    = document.getElementById('momentum-ring-fill');
        const pctEl   = document.getElementById('momentum-pct');
        const panel   = root.querySelector('.momentum-panel');
        if (!fill) return;

        const total     = parseInt(fill.dataset.total     || '0', 10);
        const completed = parseInt(fill.dataset.completed || '0', 10);
        const ratio     = total > 0 ? clamp(completed / total, 0, 1) : 0;
        const pct       = Math.round(ratio * 100);

        if (panel) panel.classList.toggle('is-empty', total === 0);

        // Bar
        if (!reduceMotion) {
            setTimeout(function() { fill.style.width = (pct) + '%'; }, 80);
        } else {
            fill.style.width = pct + '%';
        }

        // SVG ring: circumference = 2π×50 ≈ 314
        const circ = 314;
        if (ring) {
            const offset = circ - (ratio * circ);
            if (!reduceMotion) {
                setTimeout(function() { ring.style.strokeDashoffset = offset; }, 80);
            } else {
                ring.style.strokeDashoffset = offset;
            }
        }

        // Percentage text
        if (pctEl) {
            animateValue(0, pct, 1000, 0, function(v) { pctEl.textContent = Math.round(v) + '%'; });
        }
    })();

    /* ── 4. Score ring + readiness badge ────────── */
    (function initScoreRing() {
        const section = root.querySelector('.dash-insight');
        if (!section) return;

        const score  = clamp(parseFloat(section.dataset.score || '0'), 0, 10);
        const ring   = document.getElementById('score-ring-fill');
        const valEl  = document.getElementById('score-ring-value');
        const badge  = document.getElementById('insight-readiness-badge');

        // Ring: circumference = 2π×68 ≈ 427
        const circ   = 427;
        const offset = circ - (score / 10) * circ;

        if (ring) {
            // Colour by score
            const colour = score >= 7 ? 'var(--success)' : score >= 5 ? 'var(--warning)' : 'var(--danger)';
            ring.style.stroke = colour;
            if (!reduceMotion) {
                setTimeout(function() { ring.style.strokeDashoffset = offset; }, 100);
            } else {
                ring.style.strokeDashoffset = offset;
            }
        }

        if (valEl) {
            animateValue(0, score, 1000, 1, function(v) { valEl.textContent = v.toFixed(1); });
        }

        // Readiness badge
        if (badge) {
            let label, bg, col;
            if (score >= 7) {
                label = '✓ Interview ready'; bg = 'var(--success-dim)'; col = 'var(--success)';
            } else if (score >= 5) {
                label = '~ Getting there'; bg = 'var(--amber-dim)'; col = 'var(--warning)';
            } else if (score > 0) {
                label = '⚡ Needs work'; bg = 'var(--danger-dim)'; col = 'var(--danger)';
            } else {
                label = '— No data yet'; bg = 'var(--bg-3)'; col = 'var(--text-3)';
            }
            badge.textContent = label;
            badge.style.background  = bg;
            badge.style.color       = col;
            badge.style.borderColor = col;
        }

        // Highlight active tier
        root.querySelectorAll('.tier').forEach(function(tier) {
            const min = parseFloat(tier.dataset.min);
            const max = parseFloat(tier.dataset.max);
            const colour = tier.dataset.color;
            if (score >= min && score < max) {
                tier.classList.add('is-active');
                tier.querySelector('.tier-dot').style.background = colour;
            } else {
                tier.querySelector('.tier-dot').style.background = 'var(--text-3)';
            }
        });
    })();

    /* ── 5. Recent sessions: search + filter ──── */
    (function initRecentControls() {
        const stack    = document.getElementById('recent-stack');
        const emptyMsg = document.getElementById('recent-filter-empty');
        const filters  = root.querySelectorAll('.chip-filter');
        const search   = document.getElementById('recent-search');
        if (!stack) return;

        const items = Array.from(stack.querySelectorAll('.recent-item'));
        let activeFilter = 'all';
        let searchQuery  = '';

        function applyFilters() {
            let visible = 0;
            items.forEach(function(item) {
                const statusOk = activeFilter === 'all' || item.dataset.status === activeFilter;
                const title    = (item.dataset.title    || '').toLowerCase();
                const cat      = (item.dataset.category || '').toLowerCase();
                const q        = searchQuery.toLowerCase();
                const searchOk = !q || title.includes(q) || cat.includes(q);
                const show     = statusOk && searchOk;
                item.classList.toggle('is-hidden', !show);
                if (show) visible++;
            });
            if (emptyMsg) emptyMsg.hidden = visible > 0;
        }

        // Filter chips
        filters.forEach(function(btn) {
            btn.addEventListener('click', function() {
                filters.forEach(function(b) { b.classList.remove('is-active'); });
                btn.classList.add('is-active');
                activeFilter = btn.dataset.filter;
                applyFilters();
            });
        });

        // Live search
        if (search) {
            search.addEventListener('input', function() {
                searchQuery = search.value;
                applyFilters();
            });
        }
    })();

    /* ── 6. Charts ────────────────────────────── */
    (function initCharts() {
        const section = document.getElementById('dash-charts');
        if (!section) return;

        let chartData;
        try { chartData = JSON.parse(section.dataset.chart || '{}'); } catch { return; }

        const trend  = chartData.trend  || { labels: [], scores: [] };
        const topics = chartData.topics || { labels: [], scores: [], counts: [] };

        const style   = getComputedStyle(document.documentElement);
        const primary = style.getPropertyValue('--primary').trim() || '#8b6fff';
        const success = style.getPropertyValue('--success').trim() || '#00ffb3';
        const text2   = style.getPropertyValue('--text-2').trim()  || '#8f8aad';
        const border  = style.getPropertyValue('--border').trim()  || 'rgba(130,100,255,.15)';
        const surface = style.getPropertyValue('--surface').trim() || 'rgba(14,14,26,.88)';

        const baseFont   = { family: 'JetBrains Mono, Inter, monospace', size: 11 };
        const gridColor  = 'rgba(148,163,184,0.10)';
        const tooltipCfg = {
            backgroundColor: surface,
            titleColor: primary,
            bodyColor: text2,
            borderColor: border,
            borderWidth: 1,
            padding: 12,
            cornerRadius: 8,
        };

        // Tab switcher
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

        // Load Chart.js then draw
        function draw() {
            /* 1. Trend line */
            const trendEmpty = document.getElementById('chart-trend-empty');
            const trendWrap  = document.getElementById('chart-trend-wrap');
            if (!trend.scores || !trend.scores.length) {
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
                            pointHoverRadius: 7,
                            fill: true,
                            tension: 0.38,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        animation: { duration: reduceMotion ? 0 : 900, easing: 'easeOutQuart' },
                        plugins: {
                            legend: { display: false },
                            tooltip: Object.assign({}, tooltipCfg, {
                                callbacks: { label: function(c) { return ' Score: ' + c.parsed.y + ' / 10'; } },
                            }),
                        },
                        scales: {
                            x: { grid: { color: gridColor }, ticks: { color: text2, font: baseFont }, border: { color: border } },
                            y: { min: 0, max: 10, grid: { color: gridColor }, ticks: { color: text2, font: baseFont, stepSize: 2 }, border: { color: border } },
                        },
                    },
                });
            }

            /* 2. Topics bar */
            const topicsEmpty = document.getElementById('chart-topics-empty');
            const topicsWrap  = document.getElementById('chart-topics-wrap');
            if (!topics.scores || !topics.scores.length) {
                if (topicsEmpty) topicsEmpty.hidden = false;
                if (topicsWrap)  topicsWrap.hidden  = true;
            } else {
                const barColors = topics.scores.map(function(s) {
                    return s >= 7 ? '#10b981' : s >= 5 ? '#f59e0b' : '#ef4444';
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
                            borderSkipped: false,
                        }],
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: true,
                        animation: { duration: reduceMotion ? 0 : 900, easing: 'easeOutQuart' },
                        plugins: {
                            legend: { display: false },
                            tooltip: Object.assign({}, tooltipCfg, {
                                callbacks: {
                                    label: function(c) {
                                        const i = c.dataIndex;
                                        return ' ' + c.parsed.x + '/10  (' + (topics.counts[i] || 0) + ' sessions)';
                                    },
                                },
                            }),
                        },
                        scales: {
                            x: { min: 0, max: 10, grid: { color: gridColor }, ticks: { color: text2, font: baseFont, stepSize: 2 }, border: { color: border } },
                            y: { grid: { display: false }, ticks: { color: text2, font: baseFont }, border: { color: 'transparent' } },
                        },
                    },
                });
            }
        }

        if (window.Chart) {
            draw();
        } else {
            var s = document.createElement('script');
            s.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
            s.onload = draw;
            document.head.appendChild(s);
        }
    })();

})();
