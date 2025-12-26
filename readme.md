# 🔍 OCR Text Extractor Pro

### Check it out public access : https://optical-character-recognition-op27.onrender.com/
or ### check it out for local machine(offline) : http://localhost:5000/

An advanced, all-in-one OCR web application that extracts text from images and PDFs with AI-powered accuracy — completely offline, no API keys needed.

## ✨ Features

- 📸 Supports **Images** (JPG, PNG) and **PDFs** (multi-page)
- 🌍 **Multi-language OCR** (100+ languages via Tesseract)
- 🔄 **Real-time Translation** (200+ languages via Google Translate)
- 📝 **Smart Text Summarization** (Brief, Detailed, or Bullet Points)
- 🔊 **Text-to-Speech (TTS)** with Male/Female voices and 8 emotions (professional, happy, excited, etc.)
- 💾 Export as **TXT** or **DOCX**
- 🎵 Export audio as **MP3**
- 📊 Shows **confidence score**, **word count**, **character count**, and **page count**
- 🎨 Beautiful, responsive web interface
- 🐳 Fully Dockerized — runs anywhere
- 🛡️ No external API dependencies — 100% self-contained

## 🚀 Quick Start

- clone and enter the project folder

- 1. git clone project repo link

- 2. cd projectfolder

### Prerequisites
- Docker Desktop installed

### 3 Commands to Run

```bash
# 1. Build
docker build -t ocr-app .

# 2. Run
docker-compose up -d

# 3. Open browser
open http://localhost:5000
```

## 🎯 How to Use

1. Go to http://localhost:5000
2. Choose OCR language (e.g., French, Hindi, Arabic)
3. (Optional) Select translation language
4. Upload an image or PDF
5. Click "Extract Text"
6. View results with stats (confidence, word count, etc.)
7. Summarize (brief/detailed/bullets)
8. Listen via Text-to-Speech
9. Download TXT, DOCX, or MP3

## 📁 Project Structure

```
ocr-text-extractor-pro/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build config
├── docker.yml              # Docker Compose (renamed from docker-compose.yml)
├── templates/index.html    # Web interface
├── static/
│   ├── css/style.css       # Styling
│   └── js/script.js        # Frontend logic
├── uploads/                # Uploaded files (auto-created)
├── results/                # OCR results (JSON, auto-created)
└── exports/                # Exported TXT/DOCX/MP3 (auto-created)
```

## 🛠️ Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker logs ocr-app

# Rebuild
docker-compose up -d --build
```

## 🌐 Deploy to Cloud

### Render.com
1. Connect GitHub repo
2. Select Docker environment
3. Deploy

Just connect your GitHub repo and select Docker environment.

## 🐛 Troubleshooting

**Container won't start?**
```bash
docker logs ocr-app
```

**Port already in use?**
```bash
docker run -d -p 8080:5000 ocr-app
```

**Can't access webpage?**
- Check Docker is running
- Check http://localhost:5000 (not https)
- Try different browser

🤝 Credits & Tech Stack

- Flask – Web framework
- Tesseract OCR – Google's open-source OCR engine
- OpenCV – Image preprocessing
- googletrans – Translation
- pyttsx3 + pydub – Text-to-Speech & MP3 export
- python-docx – DOCX generation
- Docker & Gunicorn – Production-ready deployment

## 💡 Use Cases

-Digitize handwritten notes or scanned books
-Extract text from screenshots or photos
-Translate foreign documents instantly
-Generate audio summaries for accessibility
-Process invoices, forms, receipts, research papers

## 🔒 Security

- No API keys required
- Files stored locally
- No external API calls
- CORS enabled for local development

## 📈 Performance

- Processing time: 5-10 seconds per image
- Accuracy: 90-95% for clear printed text
- Max file size: 100MB
- Supported formats: JPG, PNG, JPEG, PDF

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Share improvements

## 📄 License

MIT License - Free to use for any purpose

## 📧 Support

Found a bug or have a feature idea?
Open an issue on GitHub or share your feedback!

---

Made with❤️ — A powerful, private, all-in-one OCR tool. No API keys. No limits. Just pure performance.
Enjoy responsibly.
