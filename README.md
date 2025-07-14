# Intelligent File Processing Agent

A powerful web application that processes various file types and provides AI-powered summaries with security analysis using OpenAI's GPT models.

## Features

- **Universal File Support**: PDF, DOC, DOCX, TXT, Images, Excel, PowerPoint, Key files, JSON, XML, YAML, HTML, and more
- **AI-Powered Summaries**: Intelligent content analysis using OpenAI GPT-4
- **Security Analysis**: Detects sensitive information (PII, credentials, financial data)
- **Real-time Processing**: Instant file analysis and summary generation
- **Modern Web Interface**: Responsive design with drag-and-drop functionality
- **Content Masking**: Automatically redacts sensitive information

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd intelligent-file-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. System Dependencies

Install system dependencies for OCR and document processing:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

**Windows:**