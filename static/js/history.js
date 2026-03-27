(function () {
    const page = document.querySelector('[data-page="history"]');
    if (!page) return;

    const filters    = page.querySelectorAll('.chip-filter');
    const cards      = Array.from(page.querySelectorAll('.recent-item'));
    const emptyState = page.querySelector('#history-filter-empty');

    /* ──────────────────────────────────────────────────
       Feature 3 — Search & filter history
       Status chip filters + text search + category,
       difficulty and score range dropdowns all work
       together. Each card stores its attributes in
       data-* so nothing needs a round-trip to the server.
    ────────────────────────────────────────────────── */
    const searchInput  = document.getElementById('history-search');
    const clearBtn     = document.getElementById('history-search-clear');
    const catSel       = document.getElementById('history-cat-filter');
    const diffSel      = document.getElementById('history-diff-filter');
    const scoreSel     = document.getElementById('history-score-filter');
    const countLabel   = document.getElementById('history-result-count');

    let activeStatus = 'all';

    function scoreMatch(card, scoreFilter) {
        if (!scoreFilter) return true;
        const raw = card.dataset.score;
        if (scoreFilter === 'none') return raw === '' || raw === undefined;
        const val = parseFloat(raw);
        if (isNaN(val)) return false;
        if (scoreFilter === 'high') return val >= 7;
        if (scoreFilter === 'mid')  return val >= 5 && val < 7;
        if (scoreFilter === 'low')  return val < 5;
        return true;
    }

    function applyAll() {
        const query  = (searchInput ? searchInput.value.toLowerCase().trim() : '');
        const cat    = catSel  ? catSel.value  : '';
        const diff   = diffSel ? diffSel.value : '';
        const score  = scoreSel ? scoreSel.value : '';
        let visible  = 0;

        cards.forEach(function(card) {
            const statusOk = activeStatus === 'all' || card.dataset.status === activeStatus;
            const catOk    = !cat  || card.dataset.category  === cat;
            const diffOk   = !diff || card.dataset.difficulty === diff;
            const scoreOk  = scoreMatch(card, score);
            const title    = (card.dataset.title || '') + ' ' + (card.dataset.category || '');
            const searchOk = !query || title.includes(query);

            const show = statusOk && catOk && diffOk && scoreOk && searchOk;
            card.classList.toggle('is-hidden', !show);
            if (show) visible++;
        });

        if (emptyState) emptyState.hidden = visible !== 0;
        if (countLabel) countLabel.textContent = visible + ' session' + (visible === 1 ? '' : 's');
    }

    /* Status chip filters */
    if (filters.length) {
        filters.forEach(function(button) {
            button.addEventListener('click', function() {
                activeStatus = button.dataset.filter || 'all';
                filters.forEach(function(f) { f.classList.remove('is-active'); });
                button.classList.add('is-active');
                applyAll();
            });
        });
    }

    /* Search box */
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            if (clearBtn) clearBtn.hidden = !searchInput.value;
            applyAll();
        });
    }
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            clearBtn.hidden = true;
            applyAll();
        });
    }

    /* Dropdown filters */
    [catSel, diffSel, scoreSel].forEach(function(sel) {
        if (sel) sel.addEventListener('change', applyAll);
    });

    /* Initial count */
    applyAll();
})();
