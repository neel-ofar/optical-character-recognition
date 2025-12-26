const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const ocrLang = document.getElementById('ocrLang');
const translateTo = document.getElementById('translateTo');
const processBtn = document.getElementById('processBtn');
const preview = document.getElementById('preview');
const loading = document.getElementById('loading');
const loadingMessage = document.getElementById('loadingMessage');
const resultBox = document.getElementById('resultBox');
const textOutput = document.getElementById('textOutput');
const confidenceBadge = document.getElementById('confidenceBadge');
const resultTitle = document.getElementById('resultTitle');
const downloadTxt = document.getElementById('downloadTxt');
const downloadDocx = document.getElementById('downloadDocx');
const ttsSection = document.getElementById('ttsSection');
const ttsGender = document.getElementById('ttsGender');
const ttsTone = document.getElementById('ttsTone');
const generateAudio = document.getElementById('generateAudio');
const summarizerSection = document.getElementById('summarizerSection');
const summaryMode = document.getElementById('summaryMode');
const generateSummary = document.getElementById('generateSummary');
const summaryOutput = document.getElementById('summaryOutput');

let selectedFile = null;
let currentResult = null;
let isTranslated = false;

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', e => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', e => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', e => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
});

function handleFile(file) {
    if (file.size > 100 * 1024 * 1024) {
        alert('❌ File too large! Max 100MB');
        return;
    }
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
    if (!validTypes.includes(file.type)) {
        alert('❌ Invalid file type!');
        return;
    }
    selectedFile = file;
    processBtn.disabled = false;
    resultBox.style.display = 'none';
    ttsSection.style.display = 'none';

    if (file.type === 'application/pdf') {
        preview.innerHTML = `<div style="padding:40px;background:#f8f9ff;border-radius:15px;">
            <div style="font-size:4em;margin-bottom:20px;">📄</div>
            <h3 style="color:#667eea;">PDF Selected</h3><p>${file.name}</p></div>`;
        loadingMessage.textContent = 'Processing PDF... This may take a while';
    } else {
        const reader = new FileReader();
        reader.onload = e => preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        reader.readAsDataURL(file);
        loadingMessage.textContent = 'Processing image...';
    }
}

processBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    loading.style.display = 'block';
    resultBox.style.display = 'none';
    processBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('ocr_lang', ocrLang.value);
    formData.append('translate_to', translateTo.value);

    try {
        const response = await fetch('/api/ocr', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.success || data.text !== undefined) {
            currentResult = data;
            isTranslated = data.translated || false;
            textOutput.textContent = data.text || 'No text detected';
            let badgeText = data.confidence.toFixed(1) + '% confidence';

            if (data.word_count !== undefined) {
                badgeText += ` • ${data.word_count} word${data.word_count !== 1 ? 's' : ''}`;
            }
            if (data.char_count !== undefined) {
                badgeText += ` • ${data.char_count.toLocaleString()} character${data.char_count !== 1 ? 's' : ''}`;
            }
            if (data.pages) {
                badgeText += ` • ${data.pages} page${data.pages !== 1 ? 's' : ''}`;
            }
            if (isTranslated) {
                badgeText += ' • Translated';
            }

            confidenceBadge.textContent = badgeText;
            if (data.pages) {
                resultTitle.innerHTML = isTranslated ? '🌍 Translated Text (PDF)' : '📄 Extracted Text (PDF)';
                confidenceBadge.textContent += ` • ${data.pages} pages`;
            } else {
                resultTitle.innerHTML = isTranslated ? '🌍 Translated Text' : '📄 Extracted Text';
            }
            if (isTranslated) confidenceBadge.textContent += ' • Translated';
            resultBox.style.display = 'block';
            ttsSection.style.display = 'block';
            summarizerSection.style.display = 'block';  
            summaryOutput.style.display = 'none';
        } else {
            alert('❌ Error: ' + (data.error || 'Processing failed'));
        }
    } catch (err) {
        alert('❌ Network error: ' + err.message);
    } finally {
        loading.style.display = 'none';
        processBtn.disabled = false;
    }
});

downloadTxt.addEventListener('click', async () => {
    await downloadFile('/api/export/txt', 'txt');
});

downloadDocx.addEventListener('click', async () => {
    await downloadFile('/api/export/docx', 'docx');
});

generateAudio.addEventListener('click', async () => {
    if (!currentResult || !currentResult.text) return;
    generateAudio.disabled = true;
    generateAudio.textContent = 'Generating audio...';
    await downloadFile('/api/tts', 'mp3', {
        text: currentResult.text,
        gender: ttsGender.value,
        tone: ttsTone.value,
        filename: selectedFile.name
    });
    generateAudio.disabled = false;
    generateAudio.textContent = '🎤 Generate & Download Audio (MP3)';
});

generateSummary.addEventListener('click', async () => {
    if (!currentResult || !currentResult.text) {
        alert('No text available to summarize');
        return;
    }
    generateSummary.disabled = true;
    generateSummary.textContent = 'Generating summary...';

    try {
        const res = await fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: currentResult.text,
                mode: summaryMode.value
            })
        });
        const data = await res.json();
        if (data.summary) {
            summaryOutput.textContent = data.summary;
            summaryOutput.style.display = 'block';
        } else {
            alert('Failed to generate summary');
        }
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        generateSummary.disabled = false;
        generateSummary.textContent = 'Generate Summary';
    }
});

async function downloadFile(endpoint, ext, extraData = {}) {
    const body = {
        text: currentResult.text,
        filename: selectedFile.name,
        translated: isTranslated,
        translate_lang: translateTo.value || null,
        ...extraData
    };
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `extracted_${isTranslated ? 'translated_' : ''}${Date.now()}.${ext}`;
            a.click();
            URL.revokeObjectURL(url);
        } else {
            alert('Download failed');
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
}
