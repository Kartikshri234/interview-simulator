(function () {
    const page = document.querySelector('[data-page="history"]');
    if (!page) return;

    const filters = page.querySelectorAll('.chip-filter');
    const cards = page.querySelectorAll('.recent-item');
    const emptyState = page.querySelector('#history-filter-empty');

    if (!filters.length || !cards.length) return;

    filters.forEach((button) => {
        button.addEventListener('click', () => {
            const selected = button.dataset.filter || 'all';
            let visible = 0;

            filters.forEach((f) => f.classList.remove('is-active'));
            button.classList.add('is-active');

            cards.forEach((card) => {
                const match = selected === 'all' || card.dataset.status === selected;
                card.classList.toggle('is-hidden', !match);
                if (match) visible += 1;
            });

            if (emptyState) emptyState.hidden = visible !== 0;
        });
    });
})();
