import os
import logging
from typing import Dict, List
import json
import re
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self):
        # Initialize OpenAI client properly
        # Make sure to export your key: export OPENAI_API_KEY="sk-..."
        self.client = OpenAI()

        # Default model to use
        self.model = "gpt-4o"

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

            # Create system and user prompts
            system_prompt = self._create_system_prompt(filename, security_flags)
            user_prompt = self._create_user_prompt(content, filename, security_flags)

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
            summary = self._sanitize_summary(summary)
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary for {filename}: {str(e)}"

    def _create_system_prompt(self, filename: str, security_flags: Dict) -> str:
        """Create system prompt"""
        base_prompt = """You are an intelligent document analysis assistant. Your task is to provide comprehensive, accurate summaries of uploaded files while maintaining strict security protocols.

SECURITY REQUIREMENTS:
- NEVER include actual sensitive information like passwords, API keys, credit card numbers, SSNs, passport numbers, or account numbers in your response
- If sensitive information is detected, acknowledge its presence but describe it generically
- For key files (PPK, PEM, etc.), focus on file type and purpose, not actual content
- Redact or mask any personally identifiable information (PII)"""

        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if file_ext == 'pdf':
            base_prompt += "\n\nFILE TYPE: PDF Document\nFocus on: Main topics, key sections, document structure."
        elif file_ext in ['doc', 'docx']:
            base_prompt += "\n\nFILE TYPE: Word Document\nFocus on: Main themes, document purpose."
        elif file_ext in ['jpg', 'jpeg', 'png']:
            base_prompt += "\n\nFILE TYPE: Image with OCR text\nFocus on: Extracted text, type of content."
        elif file_ext in ['xlsx', 'xls', 'csv']:
            base_prompt += "\n\nFILE TYPE: Spreadsheet\nFocus on: Data structure, headers, and insights."
        elif file_ext in ['ppt', 'pptx']:
            base_prompt += "\n\nFILE TYPE: Presentation\nFocus on: Key slides, topics."
        elif file_ext in ['ppk', 'pem', 'key']:
            base_prompt += "\n\nFILE TYPE: Security Key File\nFocus on: Purpose, do not show actual key."
        elif file_ext in ['json', 'xml', 'yaml', 'yml']:
            base_prompt += "\n\nFILE TYPE: Data File\nFocus on: Structure and purpose, not values."

        if security_flags.get('has_sensitive_content'):
            base_prompt += "\n\n⚠️ SECURITY ALERT: File has sensitive content. Be extra cautious."

        return base_prompt

    def _create_user_prompt(self, content: str, filename: str, security_flags: Dict) -> str:
        prompt = f"""Please analyze the following file and provide a comprehensive summary:

Filename: {filename}
Content Length: {len(content)} characters

CONTENT:
{content}

Please include:
1. File type and format
2. Main content overview
3. Key topics
4. Document structure
5. Important findings or data insights
6. Notable features

SECURITY NOTES:"""
        if security_flags.get('has_sensitive_content'):
            prompt += "\n- Contains sensitive data - describe it generically."
        if security_flags.get('detected_patterns'):
            prompt += f"\n- Detected patterns: {', '.join(security_flags['detected_patterns'])}"

        prompt += "\n\nRemember: DO NOT include actual sensitive data."
        return prompt

    def _sanitize_summary(self, summary: str) -> str:
        """Sanitize summary"""
        for pattern in self.sensitive_patterns:
            summary = re.sub(pattern, '[REDACTED]', summary, flags=re.IGNORECASE)
        sensitive_keywords = ['password', 'pwd', 'pass', 'secret', 'key', 'token', 'auth',
                              'ssn', 'social', 'account', 'card', 'number', 'pin', 'code']
        for keyword in sensitive_keywords:
            pattern = rf'{keyword}\s*[:=]\s*\S+'
            summary = re.sub(pattern, f'{keyword}: [REDACTED]', summary, flags=re.IGNORECASE)
        return summary

    def analyze_content_type(self, content: str, filename: str) -> Dict:
        """Analyze and categorize content"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a content analyzer. Return JSON with content type, language, and key characteristics."},
                    {"role": "user", "content": f"Analyze content from '{filename}':\n\n{content[:2000]}"}
                ],
                max_tokens=500,
                temperature=0.1
            )
            analysis = response.choices[0].message.content
            try:
                return json.loads(analysis)
            except:
                return {"analysis": analysis}
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            return {"error": str(e)}

    def extract_key_information(self, content: str, filename: str) -> List[str]:
        """Extract key information"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract the 5 most important key points as a numbered list."},
                    {"role": "user", "content": content[:3000]}
                ],
                max_tokens=800,
                temperature=0.2
            )
            key_points = response.choices[0].message.content
            return [line.strip() for line in key_points.split('\n') if line.strip()]
        except Exception as e:
            logger.error(f"Error extracting key information: {str(e)}")
            return [f"Error: {str(e)}"]

