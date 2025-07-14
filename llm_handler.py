import openai
import os
import logging
from typing import Dict, List, Optional
import json
import re

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self):
        # Initialize OpenAI client
        self.client = openai.OpenAI(
            api_key=os.getenv('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')
        )
        
        # Set default model
        self.model = "gpt-4-turbo-preview"
        
        # Maximum tokens for content processing
        self.max_tokens = 4000
        
        # Sensitive content patterns
        self.sensitive_patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card numbers
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',  # SSN
            r'\b[A-Z]{2}\d{6}[A-Z]\b',  # Passport numbers
            r'\b\d{10,}\b',  # Account numbers
            r'password\s*[:=]\s*\S+',  # Passwords
            r'api[_\s]?key\s*[:=]\s*\S+',  # API keys
        ]
    
    def generate_summary(self, content: str, filename: str, security_flags: Dict) -> str:
        """Generate intelligent summary of file content"""
        try:
            # Truncate content if too long
            if len(content) > 10000:
                content = content[:10000] + "... [Content truncated]"
            
            # Create system prompt based on file type and security flags
            system_prompt = self._create_system_prompt(filename, security_flags)
            
            # Create user prompt
            user_prompt = self._create_user_prompt(content, filename, security_flags)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content
            
            # Post-process summary to ensure no sensitive data leaks
            summary = self._sanitize_summary(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary for {filename}: {str(e)}"
    
    def _create_system_prompt(self, filename: str, security_flags: Dict) -> str:
        """Create system prompt based on file type and security context"""
        
        base_prompt = """You are an intelligent document analysis assistant. Your task is to provide comprehensive, accurate summaries of uploaded files while maintaining strict security protocols.

SECURITY REQUIREMENTS:
- NEVER include actual sensitive information like passwords, API keys, credit card numbers, SSNs, passport numbers, or account numbers in your response
- If sensitive information is detected, acknowledge its presence but describe it generically (e.g., "contains credit card information" instead of showing the actual number)
- For key files (PPK, PEM, etc.), focus on the file type and purpose, not the actual key content
- Redact or mask any personally identifiable information (PII)"""
        
        # Add file-specific instructions
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext == 'pdf':
            base_prompt += "\n\nFILE TYPE: PDF Document\nFocus on: Main topics, key sections, document structure, and important findings."
        elif file_ext in ['doc', 'docx']:
            base_prompt += "\n\nFILE TYPE: Word Document\nFocus on: Content overview, main themes, document purpose, and key information."
        elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
            base_prompt += "\n\nFILE TYPE: Image with OCR text\nFocus on: Describe what text was extracted, image content type, and any readable information."
        elif file_ext in ['xlsx', 'xls', 'csv']:
            base_prompt += "\n\nFILE TYPE: Spreadsheet\nFocus on: Data structure, column headers, data types, and insights without showing actual sensitive data."
        elif file_ext in ['ppt', 'pptx']:
            base_prompt += "\n\nFILE TYPE: Presentation\nFocus on: Main topics, slide structure, key points, and presentation purpose."
        elif file_ext in ['ppk', 'pem', 'key']:
            base_prompt += "\n\nFILE TYPE: Security Key File\nFocus on: Key type, purpose, and security considerations. DO NOT include actual key content."
        elif file_ext in ['json', 'xml', 'yaml', 'yml']:
            base_prompt += "\n\nFILE TYPE: Data File\nFocus on: Data structure, key fields, and purpose while protecting sensitive values."
        
        # Add security-specific instructions
        if security_flags.get('has_sensitive_content', False):
            base_prompt += "\n\n⚠️ SECURITY ALERT: This file contains sensitive information. Be extra cautious about information disclosure."
        
        return base_prompt
    
    def _create_user_prompt(self, content: str, filename: str, security_flags: Dict) -> str:
        """Create user prompt with content and specific instructions"""
        
        prompt = f"""Please analyze the following file and provide a comprehensive summary:

Filename: {filename}
Content Length: {len(content)} characters

CONTENT:
{content}

Please provide a summary that includes:
1. File type and format
2. Main content overview
3. Key topics or themes
4. Document structure or organization
5. Important findings or data insights
6. Any notable features or characteristics

SECURITY NOTES:"""
        
        if security_flags.get('has_sensitive_content', False):
            prompt += "\n- This file contains sensitive information - describe it generically"
        
        if security_flags.get('detected_patterns'):
            prompt += f"\n- Detected patterns: {', '.join(security_flags['detected_patterns'])}"
        
        prompt += "\n\nRemember: DO NOT include actual sensitive data in your response."
        
        return prompt
    
    def _sanitize_summary(self, summary: str) -> str:
        """Remove any sensitive information that might have leaked into the summary"""
        
        # Remove potential sensitive patterns
        for pattern in self.sensitive_patterns:
            summary = re.sub(pattern, '[REDACTED]', summary, flags=re.IGNORECASE)
        
        # Remove common sensitive keywords followed by values
        sensitive_keywords = [
            'password', 'pwd', 'pass', 'secret', 'key', 'token', 'auth',
            'ssn', 'social', 'account', 'card', 'number', 'pin', 'code'
        ]
        
        for keyword in sensitive_keywords:
            pattern = rf'{keyword}\s*[:=]\s*\S+'
            summary = re.sub(pattern, f'{keyword}: [REDACTED]', summary, flags=re.IGNORECASE)
        
        return summary
    
    def analyze_content_type(self, content: str, filename: str) -> Dict:
        """Analyze and categorize content type"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a content analyzer. Analyze the provided content and return a JSON object with content type, language, and key characteristics."},
                    {"role": "user", "content": f"Analyze this content from file '{filename}':\n\n{content[:2000]}"}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text description
            try:
                return json.loads(analysis)
            except:
                return {"analysis": analysis}
                
        except Exception as e:
            logger.error(f"Error analyzing content type: {str(e)}")
            return {"error": str(e)}
    
    def extract_key_information(self, content: str, filename: str) -> List[str]:
        """Extract key information points from content"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract the 5 most important key points from the provided content. Return as a numbered list."},
                    {"role": "user", "content": content[:3000]}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            key_points = response.choices[0].message.content
            return key_points.split('\n') if key_points else []
            
        except Exception as e:
            logger.error(f"Error extracting key information: {str(e)}")
            return [f"Error extracting key information: {str(e)}"]