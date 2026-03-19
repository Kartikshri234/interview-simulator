window.getCsrfToken = function () {
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith('csrftoken=')) {
            return decodeURIComponent(trimmed.slice('csrftoken='.length));
        }
    }
    return '';
};
