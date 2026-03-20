(function () {
    const page = document.querySelector('[data-page="results"]');
    if (!page) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function clamp(value, min, max) {
        return Math.min(max, Math.max(min, value));
    }

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
})();
