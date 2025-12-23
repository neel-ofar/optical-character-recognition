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

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create directories
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(RESULTS_FOLDER).mkdir(exist_ok=True)

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

def extract_text(image_path):
    """Extract text from image using Tesseract OCR"""
    try:
        # Load image
        image = cv2.imread(image_path)
        
        # Preprocess
        processed = preprocess_image(image)
        
        # Extract text
        text = pytesseract.image_to_string(processed)
        
        # Get confidence
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

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Application</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
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
        .upload-icon { 
            font-size: 4em; 
            margin-bottom: 20px; 
        }
        input[type="file"] { display: none; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            transition: all 0.3s;
            width: 100%;
        }
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
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
        }
        .confidence-badge {
            display: inline-block;
            padding: 8px 20px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            margin-left: 10px;
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
        .download-btn {
            background: #10b981;
            color: white;
            border: none;
            padding: 10px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 15px;
            transition: all 0.3s;
        }
        .download-btn:hover {
            background: #059669;
            transform: translateY(-2px);
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
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 OCR Text Extractor</h1>
        <p class="subtitle">Extract text from images using AI-powered OCR</p>
        
        <div class="info-box">
            ℹ️ <strong>Free Version</strong> - Supports JPG and PNG images up to 16MB
        </div>
        
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <h2>Drop your image here or click to browse</h2>
            <p style="margin-top: 10px; color: #666;">Supports: JPG, PNG (Max 16MB)</p>
            <input type="file" id="fileInput" accept="image/jpeg,image/jpg,image/png">
        </div>
        
        <button class="btn" id="processBtn" disabled>🚀 Extract Text</button>
        
        <div class="preview" id="preview"></div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="font-size: 18px; color: #667eea; font-weight: bold;">Processing your image...</p>
        </div>
        
        <div class="result-box" id="resultBox">
            <h3>
                📄 Extracted Text
                <span class="confidence-badge" id="confidenceBadge"></span>
            </h3>
            <div class="text-output" id="textOutput"></div>
            <button class="download-btn" id="downloadBtn">💾 Download as Text File</button>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const processBtn = document.getElementById('processBtn');
        const preview = document.getElementById('preview');
        const loading = document.getElementById('loading');
        const resultBox = document.getElementById('resultBox');
        const textOutput = document.getElementById('textOutput');
        const confidenceBadge = document.getElementById('confidenceBadge');
        const downloadBtn = document.getElementById('downloadBtn');
        
        let selectedFile = null;
        let extractedText = '';

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
            if (file.size > 16 * 1024 * 1024) {
                alert('❌ File too large! Maximum size is 16MB');
                return;
            }
            
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                alert('❌ Invalid file type! Please upload JPG or PNG');
                return;
            }
            
            selectedFile = file;
            processBtn.disabled = false;
            resultBox.style.display = 'none';
            
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.innerHTML = '<img src="' + e.target.result + '" alt="Preview">';
            };
            reader.readAsDataURL(file);
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
                    extractedText = data.text;
                    textOutput.textContent = data.text || 'No text found in image';
                    confidenceBadge.textContent = data.confidence.toFixed(1) + '% confidence';
                    resultBox.style.display = 'block';
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to process image'));
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            } finally {
                loading.style.display = 'none';
                processBtn.disabled = false;
            }
        });

        downloadBtn.addEventListener('click', () => {
            const blob = new Blob([extractedText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'extracted_text_' + Date.now() + '.txt';
            a.click();
            URL.revokeObjectURL(url);
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
    """Process uploaded image and extract text"""
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
        
        # Extract text
        result = extract_text(filepath)
        
        # Save result
        if result['success']:
            result_data = {
                'timestamp': timestamp,
                'filename': saved_filename,
                'text': result['text'],
                'confidence': result['confidence']
            }
            result_file = os.path.join(
                app.config['RESULTS_FOLDER'], 
                f"result_{timestamp}.json"
            )
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'version': '1.0',
        'free_version': True
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
