// モード切り替え
const uploadModeBtn = document.getElementById('uploadModeBtn');
const searchModeBtn = document.getElementById('searchModeBtn');
const uploadMode = document.getElementById('uploadMode');
const searchMode = document.getElementById('searchMode');

uploadModeBtn.addEventListener('click', () => {
    uploadModeBtn.classList.add('active');
    searchModeBtn.classList.remove('active');
    uploadMode.classList.remove('hidden');
    searchMode.classList.add('hidden');
});

searchModeBtn.addEventListener('click', () => {
    searchModeBtn.classList.add('active');
    uploadModeBtn.classList.remove('active');
    searchMode.classList.remove('hidden');
    uploadMode.classList.add('hidden');
});

// === 画像登録モード ===
const uploadDropZone = document.getElementById('uploadDropZone');
const uploadInput = document.getElementById('uploadInput');
const uploadPreview = document.getElementById('uploadPreview');
const uploadForm = document.getElementById('uploadForm');
const uploadMessage = document.getElementById('uploadMessage');

let uploadFile = null;

// ドロップゾーンのクリック
uploadDropZone.addEventListener('click', () => uploadInput.click());

// ファイル選択
uploadInput.addEventListener('change', (e) => {
    handleUploadFile(e.target.files[0]);
});

// ドラッグ&ドロップ
uploadDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadDropZone.classList.add('drag-over');
});

uploadDropZone.addEventListener('dragleave', () => {
    uploadDropZone.classList.remove('drag-over');
});

uploadDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadDropZone.classList.remove('drag-over');
    handleUploadFile(e.dataTransfer.files[0]);
});

function handleUploadFile(file) {
    if (!file || !file.type.startsWith('image/')) {
        showMessage(uploadMessage, '画像ファイルを選択してください', 'error');
        return;
    }

    uploadFile = file;

    // プレビュー表示
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadPreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        uploadPreview.classList.remove('hidden');
        uploadForm.classList.remove('hidden');
        uploadMessage.classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

// フォーム送信
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!uploadFile) {
        showMessage(uploadMessage, '画像を選択してください', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('name', document.getElementById('imageName').value);
    formData.append('description', document.getElementById('imageDescription').value);
    formData.append('tags', document.getElementById('imageTags').value);

    try {
        const response = await fetch('/api/images', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(uploadMessage, '画像が正常に登録されました！', 'success');
            uploadForm.reset();
            uploadPreview.classList.add('hidden');
            uploadForm.classList.add('hidden');
            uploadFile = null;
        } else {
            showMessage(uploadMessage, `エラー: ${data.detail}`, 'error');
        }
    } catch (error) {
        showMessage(uploadMessage, `エラー: ${error.message}`, 'error');
    }
});

// === 画像検索モード ===
const searchDropZone = document.getElementById('searchDropZone');
const searchInput = document.getElementById('searchInput');
const searchPreview = document.getElementById('searchPreview');
const searchBtn = document.getElementById('searchBtn');
const searchMessage = document.getElementById('searchMessage');
const searchResults = document.getElementById('searchResults');
const resultsGrid = document.getElementById('resultsGrid');

let searchFile = null;

// ドロップゾーンのクリック
searchDropZone.addEventListener('click', () => searchInput.click());

// ファイル選択
searchInput.addEventListener('change', (e) => {
    handleSearchFile(e.target.files[0]);
});

// ドラッグ&ドロップ
searchDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    searchDropZone.classList.add('drag-over');
});

searchDropZone.addEventListener('dragleave', () => {
    searchDropZone.classList.remove('drag-over');
});

searchDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    searchDropZone.classList.remove('drag-over');
    handleSearchFile(e.dataTransfer.files[0]);
});

function handleSearchFile(file) {
    if (!file || !file.type.startsWith('image/')) {
        showMessage(searchMessage, '画像ファイルを選択してください', 'error');
        return;
    }

    searchFile = file;

    // プレビュー表示
    const reader = new FileReader();
    reader.onload = (e) => {
        searchPreview.innerHTML = `<img src="${e.target.result}" alt="Search">`;
        searchPreview.classList.remove('hidden');
        searchBtn.classList.remove('hidden');
        searchMessage.classList.add('hidden');
        searchResults.classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

// 検索実行
searchBtn.addEventListener('click', async () => {
    if (!searchFile) {
        showMessage(searchMessage, '画像を選択してください', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', searchFile);

    // ローディング表示
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<span class="loading"></span> 検索中...';

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            displaySearchResults(data.results);
            searchMessage.classList.add('hidden');
        } else {
            showMessage(searchMessage, `エラー: ${data.detail}`, 'error');
        }
    } catch (error) {
        showMessage(searchMessage, `エラー: ${error.message}`, 'error');
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = '検索する';
    }
});

function displaySearchResults(results) {
    resultsGrid.innerHTML = '';

    if (results.length === 0) {
        showMessage(searchMessage, '検索結果が見つかりませんでした', 'error');
        return;
    }

    results.forEach(result => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';

        const similarityPercent = (result.similarity_score * 100).toFixed(1);

        const tags = result.metadata.tags && result.metadata.tags.length > 0
            ? result.metadata.tags.map(tag => `<span class="tag">${tag}</span>`).join('')
            : '';

        resultItem.innerHTML = `
            <img src="${result.image_url}" alt="${result.metadata.name || '画像'}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22250%22 height=%22200%22><rect fill=%22%23ddd%22 width=%22250%22 height=%22200%22/><text x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 fill=%22%23999%22>No Image</text></svg>'">
            <div class="result-info">
                <div class="similarity-score">${similarityPercent}% 一致</div>
                <div class="result-metadata">
                    ${result.metadata.name ? `<h3>${result.metadata.name}</h3>` : ''}
                    ${result.metadata.description ? `<p>${result.metadata.description}</p>` : ''}
                    ${tags ? `<div class="result-tags">${tags}</div>` : ''}
                </div>
            </div>
        `;

        resultsGrid.appendChild(resultItem);
    });

    searchResults.classList.remove('hidden');
}

// ユーティリティ関数
function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `message ${type}`;
    element.classList.remove('hidden');
}
