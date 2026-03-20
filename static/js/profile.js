(function () {
    const zone = document.getElementById('avatar-drop-zone');
    const input = document.getElementById('avatar-input');
    const previewWrap = document.getElementById('avatar-preview-wrap');
    const previewImg = document.getElementById('avatar-preview-img');
    const placeholder = document.getElementById('avatar-placeholder-zone');
    const clearBtn = document.getElementById('avatar-clear-btn');

    if (!zone || !input || !previewWrap || !previewImg || !placeholder || !clearBtn) return;

    function showPreview(file) {
        if (!file || !file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = function (event) {
            previewImg.src = event.target.result;
            previewWrap.style.display = 'block';
            placeholder.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    function clearPreview() {
        previewWrap.style.display = 'none';
        placeholder.style.display = 'flex';
        previewImg.src = '';
        input.value = '';
    }

    input.addEventListener('change', function () {
        if (input.files && input.files[0]) showPreview(input.files[0]);
    });

    clearBtn.addEventListener('click', function (event) {
        event.stopPropagation();
        clearPreview();
    });

    zone.addEventListener('dragover', function (event) {
        event.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', function () {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', function (event) {
        event.preventDefault();
        zone.classList.remove('drag-over');

        const file = event.dataTransfer.files[0];
        if (!file) return;

        const transfer = new DataTransfer();
        transfer.items.add(file);
        input.files = transfer.files;
        showPreview(file);
    });
})();
