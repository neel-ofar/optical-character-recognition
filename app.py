from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
from datetime import datetime
import json
from werkzeug.utils import secure_filename
from pathlib import Path
import io
from pdf2image import convert_from_path
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import tempfile

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
EXPORT_FOLDER = 'exports'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['EXPORT_FOLDER'] = EXPORT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create directories
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(RESULTS_FOLDER).mkdir(exist_ok=True)
Path(EXPORT_FOLDER).mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image):
    """Enhance image quality for better OCR"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    return thresh

def extract_text_from_image(image_path):
    """Extract text from image using Tesseract OCR"""
    try:
        image = cv2.imread(image_path)
        processed = preprocess_image(image)
        text = pytesseract.image_to_string(processed)
        data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in data['conf'] if c != '-1']
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return {
            'text': text.strip(),
            'confidence': float(avg_confidence),
            'success': True
        }
    except Exception as e:
        return {
            'text': '',
            'confidence': 0,
            'success': False,
            'error': str(e)
        }

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF by converting to images"""
    try:
        all_text = []
        total_confidence = []
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        for i, image in enumerate(images):
            # Save temporary image
            temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            image.save(temp_image.name, 'PNG')
            
            # Extract text
            result = extract_text_from_image(temp_image.name)
            
            if result['success']:
                all_text.append(f"\n=== Page {i+1} ===\n{result['text']}")
                total_confidence.append(result['confidence'])
            
            # Cleanup
            os.unlink(temp_image.name)
        
        combined_text = '\n'.join(all_text)
        avg_confidence = np.mean(total_confidence) if total_confidence else 0
        
        return {
            'text': combined_text.strip(),
            'confidence': float(avg_confidence),
            'pages': len(images),
            'success': True
        }
    except Exception as e:
        return {
            'text': '',
            'confidence': 0,
            'pages': 0,
            'success': False,
            'error': str(e)
        }

def create_word_document(text, filename):
    """Create a Word document from text"""
    doc = Document()
    
    # Add title
    title = doc.add_heading('OCR Extracted Text', 0)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    # Add metadata
    meta = doc.add_paragraph()
    meta.add_run(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n').italic = True
    meta.add_run(f'Source: {filename}\n').italic = True
    
    # Add extracted text
    doc.add_heading('Extracted Content', level=1)
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        if para.strip():
            p = doc.add_paragraph(para.strip())
            p.style.font.size = Pt(11)
    
    # Save to temporary location
    output_path = os.path.join(
        app.config['EXPORT_FOLDER'], 
        f"{filename.rsplit('.', 1)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    )
    doc.save(output_path)
    
    return output_path

def create_text_file(text, filename):
    """Create a text file from extracted text"""
    output_path = os.path.join(
        app.config['EXPORT_FOLDER'], 
        f"{filename.rsplit('.', 1)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"OCR Extracted Text\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {filename}\n\n")
        f.write(f"{'='*50}\n\n")
        f.write(text)
    
    return output_path

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Text Extractor Pro</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .feature-badge {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8ebff 100%);
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            font-size: 14px;
            color: #667eea;
            font-weight: 600;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 60px 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 30px;
            background: #f8f9ff;
        }
        .upload-area:hover {
            background: #e8ebff;
            border-color: #764ba2;
            transform: translateY(-2px);
        }
        .upload-area.dragover {
            background: #d0d5ff;
            border-color: #764ba2;
            transform: scale(1.02);
        }
        .upload-icon { font-size: 4em; margin-bottom: 20px; }
        input[type="file"] { display: none; }
        .btn-group {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        .btn {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-secondary {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }
        .preview {
            margin: 30px 0;
            text-align: center;
        }
        .preview img {
            max-width: 100%;
            max-height: 400px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result-box {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8ebff 100%);
            padding: 30px;
            border-radius: 15px;
            margin-top: 30px;
            border-left: 5px solid #667eea;
            display: none;
        }
        .result-box h3 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .badge {
            display: inline-block;
            padding: 8px 20px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 14px;
        }
        .badge.pdf {
            background: #ef4444;
        }
        .text-output {
            background: white;
            padding: 25px;
            border-radius: 10px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.8;
            color: #333;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.05);
            margin-top: 15px;
        }
        .download-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }
        .download-btn {
            background: #10b981;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            transition: all 0.3s;
            font-weight: 600;
        }
        .download-btn:hover {
            background: #059669;
            transform: translateY(-2px);
        }
        .download-btn.word {
            background: #2563eb;
        }
        .download-btn.word:hover {
            background: #1d4ed8;
        }
        .info-box {
            background: #fef3c7;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #f59e0b;
        }
        @media (max-width: 768px) {
            .container { padding: 20px; }
            h1 { font-size: 2em; }
            .features { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 OCR Text Extractor Pro</h1>
        <p class="subtitle">Extract text from images and PDFs with multiple export formats</p>
        
        <div class="features">
            <div class="feature-badge">📸 Images (JPG, PNG)</div>
            <div class="feature-badge">📄 PDF Documents</div>
            <div class="feature-badge">📝 Export to TXT</div>
            <div class="feature-badge">📋 Export to DOCX</div>
        </div>
        
        <div class="info-box">
            ℹ️ <strong>Enhanced Version</strong> - Now supports PDF files and exports to TXT & DOCX formats!
        </div>
        
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <h2>Drop your file here or click to browse</h2>
            <p style="margin-top: 10px; color: #666;">Supports: JPG, PNG, PDF (Max 50MB)</p>
            <input type="file" id="fileInput" accept="image/jpeg,image/jpg,image/png,application/pdf">
        </div>
        
        <button class="btn" id="processBtn" disabled>🚀 Extract Text</button>
        
        <div class="preview" id="preview"></div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="font-size: 18px; color: #667eea; font-weight: bold;">Processing your file...</p>
            <p style="color: #666; margin-top: 10px;" id="loadingMessage">This may take a moment for PDF files</p>
        </div>
        
        <div class="result-box" id="resultBox">
            <h3>
                <span id="resultTitle">📄 Extracted Text</span>
                <span class="badge" id="confidenceBadge"></span>
            </h3>
            <div class="text-output" id="textOutput"></div>
            
            <div class="download-buttons">
                <button class="download-btn" id="downloadTxt">💾 Download TXT</button>
                <button class="download-btn word" id="downloadDocx">📄 Download DOCX</button>
            </div>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
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
        
        let selectedFile = null;
        let currentResult = null;

        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files[0]) handleFile(e.target.files[0]);
        });

        function handleFile(file) {
            if (file.size > 50 * 1024 * 1024) {
                alert('❌ File too large! Maximum size is 50MB');
                return;
            }
            
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
            if (!validTypes.includes(file.type)) {
                alert('❌ Invalid file type! Please upload JPG, PNG, or PDF');
                return;
            }
            
            selectedFile = file;
            processBtn.disabled = false;
            resultBox.style.display = 'none';
            
            if (file.type === 'application/pdf') {
                preview.innerHTML = '<div style="padding: 40px; background: #f8f9ff; border-radius: 15px;"><div style="font-size: 4em; margin-bottom: 20px;">📄</div><h3 style="color: #667eea;">PDF Document Selected</h3><p style="color: #666; margin-top: 10px;">' + file.name + '</p></div>';
                loadingMessage.textContent = 'Processing PDF... This may take 1-2 minutes for multi-page documents';
            } else {
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.innerHTML = '<img src="' + e.target.result + '" alt="Preview">';
                };
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
            
            try {
                const response = await fetch('/api/ocr', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentResult = data;
                    textOutput.textContent = data.text || 'No text found in file';
                    confidenceBadge.textContent = data.confidence.toFixed(1) + '% confidence';
                    
                    if (data.pages) {
                        resultTitle.innerHTML = '📄 Extracted Text from PDF';
                        confidenceBadge.textContent += ' • ' + data.pages + ' pages';
                        confidenceBadge.classList.add('pdf');
                    } else {
                        resultTitle.innerHTML = '📄 Extracted Text';
                        confidenceBadge.classList.remove('pdf');
                    }
                    
                    resultBox.style.display = 'block';
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to process file'));
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                loading.style.display = 'none';
                processBtn.disabled = false;
            }
        });

        downloadTxt.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/export/txt', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        text: currentResult.text,
                        filename: selectedFile.name
                    })
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'extracted_text_' + Date.now() + '.txt';
                    a.click();
                    URL.revokeObjectURL(url);
                } else {
                    alert('Failed to create TXT file');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });

        downloadDocx.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/export/docx', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        text: currentResult.text,
                        filename: selectedFile.name
                    })
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'extracted_text_' + Date.now() + '.docx';
                    a.click();
                    URL.revokeObjectURL(url);
                } else {
                    alert('Failed to create DOCX file');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/ocr', methods=['POST'])
def ocr_endpoint():
    """Process uploaded file and extract text"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    try:
        # Save file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        saved_filename = f"{name}_{timestamp}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)
        
        # Extract text based on file type
        if ext.lower() == '.pdf':
            result = extract_text_from_pdf(filepath)
        else:
            result = extract_text_from_image(filepath)
        
        # Save result
        if result['success']:
            result_data = {
                'timestamp': timestamp,
                'filename': saved_filename,
                'text': result['text'],
                'confidence': result['confidence'],
                'file_type': ext.lower(),
                'pages': result.get('pages', 1)
            }
            result_file = os.path.join(
                app.config['RESULTS_FOLDER'], 
                f"result_{timestamp}.json"
            )
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/export/txt', methods=['POST'])
def export_txt():
    """Export text as TXT file"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        filename = data.get('filename', 'document')
        
        output_path = create_text_file(text, filename)
        
        return send_file(
            output_path,
            mimetype='text/plain',
            as_attachment=True,
            download_name=os.path.basename(output_path)
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/docx', methods=['POST'])
def export_docx():
    """Export text as Word document"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        filename = data.get('filename', 'document')
        
        output_path = create_word_document(text, filename)
        
        return send_file(
            output_path,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=os.path.basename(output_path)
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'features': {
            'pdf_support': True,
            'txt_export': True,
            'docx_export': True
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
