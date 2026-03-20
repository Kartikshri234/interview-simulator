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
})();
