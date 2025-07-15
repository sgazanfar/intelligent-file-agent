from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import tempfile
import shutil
from werkzeug.utils import secure_filename
from file_processor import FileProcessor
from llm_handler import LLMHandler
from security_filter import SecurityFilter
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
#app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Initialize components
file_processor = FileProcessor()
llm_handler = LLMHandler()
security_filter = SecurityFilter()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
#ALLOWED_EXTENSIONS = {
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'txt', 'rtf',  # Documents
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',  # Images
    'xlsx', 'xls', 'csv',  # Spreadsheets
    'ppt', 'pptx',  # Presentations
    'ppk', 'pem', 'key',  # Key files (handled with extra security)
    'json', 'xml', 'yaml', 'yml',  # Data files
    'md', 'html', 'htm'  # Markup files

}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not supported'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Process file
        result = process_uploaded_file(filepath, filename)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': 'Failed to process file'}), 500

def process_uploaded_file(filepath, original_filename):
    try:
        # Extract content from file
        extracted_content = file_processor.extract_content(filepath, original_filename)
        
        if not extracted_content:
            return {'error': 'Could not extract content from file'}
        
        # Check for sensitive information
        security_analysis = security_filter.analyze_content(extracted_content)
        
        # Generate summary with LLM
        summary = llm_handler.generate_summary(
            content=extracted_content,
            filename=original_filename,
            security_flags=security_analysis
        )
        
        # Prepare response
        response = {
            'filename': original_filename,
            'file_type': file_processor.get_file_type(original_filename),
            'content_length': len(extracted_content),
            'summary': summary,
            'security_analysis': security_analysis,
            'processed_at': datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in process_uploaded_file: {str(e)}")
        return {'error': f'Processing failed: {str(e)}'}

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
