import os
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import docx
import pandas as pd
import json
import yaml
import xml.etree.ElementTree as ET
from pptx import Presentation
import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

class FileProcessor:
    def __init__(self):
        self.processors = {
        'pdf': self._process_pdf,
        'doc': self._process_doc,
        'docx': self._process_docx,
        'txt': self._process_txt,
        'rtf': self._process_txt,
        'md': self._process_md,
        'html': self._process_markup,
        'htm': self._process_markup,
        'json': self._process_json,
        'xml': self._process_xml,
        'yaml': self._process_yaml,
        'yml': self._process_yaml,
        'csv': self._process_csv,
        'xls': self._process_xls,
        'xlsx': self._process_xlsx,
        'jpg': self._process_image,
        'jpeg': self._process_image,
        'png': self._process_image,
        'gif': self._process_image,
        'bmp': self._process_image,
        'tiff': self._process_image,
        'svg': self._process_vector,
        'mp3': self._process_audio,
        'wav': self._process_audio,
        'flac': self._process_audio,
        'ogg': self._process_audio,
        'm4a': self._process_audio,
        'mp4': self._process_video,
        'avi': self._process_video,
        'mov': self._process_video,
        'mkv': self._process_video,
        'zip': self._process_archive,
        'rar': self._process_archive,
        '7z': self._process_archive,
        'tar': self._process_archive,
        'gz': self._process_archive,
        'exe': self._process_executable,
        'dll': self._process_executable,
        'sh': self._process_script,
        'py': self._process_script,
        'js': self._process_script,
        'css': self._process_markup,
        'log': self._process_log,
        'epub': self._process_epub,
        'iso': self._process_disk_image,
        'dmg': self._process_disk_image,
        'ppt': self._process_presentation,
        'pptx': self._process_presentation,
        'ppk': self._process_key_file,
        'pem': self._process_key_file,
        'key': self._process_key_file,
}

    
    def extract_content(self, filepath, filename):
        """Extract content from uploaded file"""
        try:
            file_ext = self.get_file_extension(filename)
            
            if file_ext in self.processors:
                return self.processors[file_ext](filepath)
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting content from {filename}: {str(e)}")
            return None
    
    def get_file_extension(self, filename):
        """Get file extension in lowercase"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def get_file_type(self, filename):
        """Determine file type category"""
        ext = self.get_file_extension(filename)
        
        if ext in ['pdf', 'doc', 'docx', 'txt', 'rtf', 'md']:
            return 'document'
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
            return 'image'
        elif ext in ['xlsx', 'xls', 'csv']:
            return 'spreadsheet'
        elif ext in ['ppt', 'pptx']:
            return 'presentation'
        elif ext in ['ppk', 'pem', 'key']:
            return 'key_file'
        elif ext in ['json', 'xml', 'yaml', 'yml']:
            return 'data_file'
        elif ext in ['html', 'htm']:
            return 'web_page'
        else:
            return 'unknown'
    
    def _process_pdf(self, filepath):
        """Extract text from PDF"""
        try:
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return None
    
    def _process_docx(self, filepath):
        """Extract text from DOCX"""
        try:
            doc = docx.Document(filepath)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}")
            return None
    
    def _process_doc(self, filepath):
        """Extract text from DOC (requires python-docx2txt)"""
        try:
            import docx2txt
            text = docx2txt.process(filepath)
            return text
        except ImportError:
            logger.warning("docx2txt not installed, cannot process .doc files")
            return "DOC file detected but docx2txt not installed for processing"
        except Exception as e:
            logger.error(f"Error processing DOC: {str(e)}")
            return None
    
    def _process_txt(self, filepath):
        """Extract text from TXT"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                with open(filepath, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error processing TXT with latin-1: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error processing TXT: {str(e)}")
            return None
    
    def _process_rtf(self, filepath):
        """Extract text from RTF"""
        try:
            from striprtf.striprtf import rtf_to_text
            with open(filepath, 'r') as file:
                rtf_content = file.read()
            return rtf_to_text(rtf_content)
        except ImportError:
            logger.warning("striprtf not installed, cannot process RTF files")
            return "RTF file detected but striprtf not installed for processing"
        except Exception as e:
            logger.error(f"Error processing RTF: {str(e)}")
            return None
    
    def _process_image(self, filepath):
        """Extract text from image using OCR"""
        try:
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return f"Image file detected. OCR processing failed: {str(e)}"
    
    def _process_excel(self, filepath):
        """Extract text from Excel files"""
        try:
            df = pd.read_excel(filepath, sheet_name=None)
            content = []
            for sheet_name, sheet_data in df.items():
                content.append(f"Sheet: {sheet_name}")
                content.append(sheet_data.to_string())
            return '\n\n'.join(content)
        except Exception as e:
            logger.error(f"Error processing Excel: {str(e)}")
            return None
    
    def _process_csv(self, filepath):
        """Extract text from CSV"""
        try:
            df = pd.read_csv(filepath)
            return df.to_string()
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            return None
    
    def _process_ppt(self, filepath):
        """Extract text from PPT (requires python-pptx)"""
        try:
            prs = Presentation(filepath)
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Error processing PPT: {str(e)}")
            return None
    
    def _process_pptx(self, filepath):
        """Extract text from PPTX"""
        return self._process_ppt(filepath)
    
    def _process_key_file(self, filepath):
        """Process key files (PPK, PEM, etc.) with security warning"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Return a summary instead of the actual content for security
            return f"SECURITY SENSITIVE: Key file detected. File contains {len(content)} characters. Type: {self._identify_key_type(content)}"
        except Exception as e:
            logger.error(f"Error processing key file: {str(e)}")
            return "Key file detected but could not be processed"
    
    def _identify_key_type(self, content):
        """Identify type of key file"""
        if "BEGIN RSA PRIVATE KEY" in content:
            return "RSA Private Key"
        elif "BEGIN CERTIFICATE" in content:
            return "Certificate"
        elif "PuTTY-User-Key-File" in content:
            return "PuTTY Private Key"
        elif "BEGIN OPENSSH PRIVATE KEY" in content:
            return "OpenSSH Private Key"
        else:
            return "Unknown Key Type"
    
    def _process_json(self, filepath):
        """Extract content from JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Error processing JSON: {str(e)}")
            return None
    
    def _process_xml(self, filepath):
        """Extract content from XML"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            return ET.tostring(root, encoding='unicode')
        except Exception as e:
            logger.error(f"Error processing XML: {str(e)}")
            return None
    
    def _process_yaml(self, filepath):
        """Extract content from YAML"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            return yaml.dump(data, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error processing YAML: {str(e)}")
            return None
    
    def _process_html(self, filepath):
        """Extract content from HTML"""
        try:
            from bs4 import BeautifulSoup
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text()
        except ImportError:
            logger.warning("BeautifulSoup not installed, processing HTML as text")
            return self._process_txt(filepath)
        except Exception as e:
            logger.error(f"Error processing HTML: {str(e)}")
            return None