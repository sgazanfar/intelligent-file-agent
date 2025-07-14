import re
import logging
from typing import Dict, List, Tuple
import hashlib

logger = logging.getLogger(__name__)

class SecurityFilter:
    def __init__(self):
        # Define sensitive data patterns
        self.sensitive_patterns = {
            'credit_card': [
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b',  # Credit card numbers
                r'\b\d{13,19}\b'  # Generic card numbers
            ],
            'ssn': [
                r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',  # US SSN
                r'\b\d{9}\b'  # SSN without separators
            ],
            'passport': [
                r'\b[A-Z]{1,2}\d{6,9}\b',  # Passport numbers
                r'\bpassport\s*#?\s*[A-Z0-9]{6,9}\b'  # Passport with text
            ],
            'bank_account': [
                r'\b\d{8,17}\b',  # Bank account numbers
                r'\baccount\s*#?\s*\d{8,17}\b'  # Account with text
            ],
            'phone': [
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',  # US phone
                r'\b\+?[1-9]\d{6,14}\b'  # International phone
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email addresses
            ],
            'ip_address': [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'  # IP addresses
            ],
            'api_key': [
                r'\bapi[_\s]?key\s*[:=]\s*[\'"]?([A-Za-z0-9+/]{20,})[\'"]?',  # API keys
                r'\btoken\s*[:=]\s*[\'"]?([A-Za-z0-9+/]{20,})[\'"]?'  # Tokens
            ],
            'password': [
                r'\bpassword\s*[:=]\s*[\'"]?([^\s\'"]+)[\'"]?',  # Passwords
                r'\bpwd\s*[:=]\s*[\'"]?([^\s\'"]+)[\'"]?',  # Pwd
                r'\bpass\s*[:=]\s*[\'"]?([^\s\'"]+)[\'"]?'  # Pass
            ],
            'private_key': [
                r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',  # Private keys
                r'-----BEGIN\s+CERTIFICATE-----',  # Certificates
                r'PuTTY-User-Key-File',  # PuTTY keys
            ],
            'government_id': [
                r'\b[A-Z]{2}\d{6}[A-Z]?\b',  # Various government IDs
                r'\bdl\s*#?\s*[A-Z0-9]{8,15}\b'  # Driver's license
            ]
        }
        
        # Keywords that indicate sensitive content
        self.sensitive_keywords = [
            'confidential', 'secret', 'private', 'classified', 'restricted',
            'personal', 'sensitive', 'internal', 'proprietary', 'confidential',
            'password', 'login', 'credential', 'auth', 'token', 'key',
            'ssn', 'social security', 'passport', 'driver license', 'bank account',
            'credit card', 'debit card', 'financial', 'medical', 'health',
            'salary', 'income', 'tax', 'legal', 'attorney', 'lawyer'
        ]
        
        # File types that are inherently sensitive
        self.sensitive_file_types = [
            'ppk', 'pem', 'key', 'p12', 'pfx', 'jks', 'keystore'
        ]
    
    def analyze_content(self, content: str, filename: str = None) -> Dict:
        """Analyze content for sensitive information"""
        try:
            analysis = {
                'has_sensitive_content': False,
                'detected_patterns': [],
                'risk_level': 'low',
                'recommendations': [],
                'masked_content': self._mask_sensitive_content(content),
                'file_type_risk': self._assess_file_type_risk(filename) if filename else 'unknown'
            }
            
            # Check for sensitive patterns
            detected_patterns = self._detect_sensitive_patterns(content)
            analysis['detected_patterns'] = detected_patterns
            
            # Check for sensitive keywords
            sensitive_keywords_found = self._detect_sensitive_keywords(content)
            
            # Determine if content is sensitive
            if detected_patterns or sensitive_keywords_found:
                analysis['has_sensitive_content'] = True
            
            # Assess risk level
            analysis['risk_level'] = self._assess_risk_level(
                detected_patterns, 
                sensitive_keywords_found, 
                filename
            )
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(
                detected_patterns, 
                sensitive_keywords_found, 
                filename
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content security: {str(e)}")
            return {
                'has_sensitive_content': True,  # Default to safe side
                'detected_patterns': [],
                'risk_level': 'high',
                'recommendations': ['Error in security analysis - treat as sensitive'],
                'masked_content': content,
                'file_type_risk': 'unknown'
            }
    
    def _detect_sensitive_patterns(self, content: str) -> List[str]:
        """Detect sensitive data patterns in content"""
        detected = []
        
        for pattern_type, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    detected.append(pattern_type)
                    break  # Only add each type once
        
        return detected
    
    def _detect_sensitive_keywords(self, content: str) -> List[str]:
        """Detect sensitive keywords in content"""
        detected = []
        content_lower = content.lower()
        
        for keyword in self.sensitive_keywords:
            if keyword in content_lower:
                detected.append(keyword)
        
        return detected
    
    def _assess_file_type_risk(self, filename: str) -> str:
        """Assess risk level based on file type"""
        if not filename:
            return 'unknown'
        
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext in self.sensitive_file_types:
            return 'high'
        elif file_ext in ['pdf', 'doc', 'docx', 'xlsx', 'xls']:
            return 'medium'
        elif file_ext in ['txt', 'md', 'html']:
            return 'low'
        else:
            return 'unknown'
    
    def _assess_risk_level(self, detected_patterns: List[str], 
                          sensitive_keywords: List[str], 
                          filename: str) -> str:
        """Assess overall risk level"""
        risk_score = 0
        
        # Pattern-based scoring
        high_risk_patterns = ['credit_card', 'ssn', 'passport', 'bank_account', 'private_key', 'api_key']
        medium_risk_patterns = ['phone', 'email', 'password']
        
        for pattern in detected_patterns:
            if pattern in high_risk_patterns:
                risk_score += 3
            elif pattern in medium_risk_patterns:
                risk_score += 2
            else:
                risk_score += 1
        
        # Keyword-based scoring
        high_risk_keywords = ['password', 'secret', 'confidential', 'private', 'ssn', 'passport']
        for keyword in sensitive_keywords:
            if keyword in high_risk_keywords:
                risk_score += 2
            else:
                risk_score += 1
        
        # File type risk
        if filename:
            file_type_risk = self._assess_file_type_risk(filename)
            if file_type_risk == 'high':
                risk_score += 3
            elif file_type_risk == 'medium':
                risk_score += 1
        
        # Determine final risk level
        if risk_score >= 5:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(self, detected_patterns: List[str], 
                                sensitive_keywords: List[str], 
                                filename: str) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if not detected_patterns and not sensitive_keywords:
            recommendations.append("No sensitive content detected - safe to process")
            return recommendations
        
        # General recommendations
        recommendations.append("⚠️ Sensitive content detected")
        
        # Pattern-specific recommendations
        if 'credit_card' in detected_patterns:
            recommendations.append("• Credit card numbers found - ensure PCI compliance")
        
        if 'ssn' in detected_patterns:
            recommendations.append("• Social Security Numbers found - handle with extreme care")
        
        if 'passport' in detected_patterns:
            recommendations.append("• Passport numbers found - protect identity information")
        
        if 'bank_account' in detected_patterns:
            recommendations.append("• Bank account numbers found - financial data protection required")
        
        if 'private_key' in detected_patterns:
            recommendations.append("• Private keys found - secure key management required")
        
        if 'api_key' in detected_patterns:
            recommendations.append("• API keys/tokens found - revoke and rotate immediately")
        
        if 'password' in detected_patterns:
            recommendations.append("• Passwords found - change passwords immediately")
        
        # File type recommendations
        if filename:
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_ext in self.sensitive_file_types:
                recommendations.append("• Key file detected - store securely and limit access")
        
        # General security recommendations
        recommendations.append("• Do not share this content publicly")
        recommendations.append("• Use secure channels for transmission")
        recommendations.append("• Consider data encryption for storage")
        
        return recommendations
    
    def _mask_sensitive_content(self, content: str) -> str:
        """Create a masked version of content for safe processing"""
        masked_content = content
        
        # Mask credit card numbers
        masked_content = re.sub(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            '[CREDIT_CARD_MASKED]',
            masked_content
        )
        
        # Mask SSN
        masked_content = re.sub(
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
            '[SSN_MASKED]',
            masked_content
        )
        
        # Mask passport numbers
        masked_content = re.sub(
            r'\b[A-Z]{1,2}\d{6,9}\b',
            '[PASSPORT_MASKED]',
            masked_content
        )
        
        # Mask bank account numbers
        masked_content = re.sub(
            r'\b\d{8,17}\b',
            '[ACCOUNT_MASKED]',
            masked_content
        )
        
        # Mask API keys and tokens
        masked_content = re.sub(
            r'\b(api[_\s]?key|token)\s*[:=]\s*[\'"]?([A-Za-z0-9+/]{20,})[\'"]?',
            r'\1: [API_KEY_MASKED]',
            masked_content,
            flags=re.IGNORECASE
        )
        
        # Mask passwords
        masked_content = re.sub(
            r'\b(password|pwd|pass)\s*[:=]\s*[\'"]?([^\s\'"]+)[\'"]?',
            r'\1: [PASSWORD_MASKED]',
            masked_content,
            flags=re.IGNORECASE
        )
        
        return masked_content
    
    def is_safe_to_process(self, content: str, filename: str = None) -> bool:
        """Quick check if content is safe to process"""
        analysis = self.analyze_content(content, filename)
        return analysis['risk_level'] in ['low', 'medium']
    
    def get_content_hash(self, content: str) -> str:
        """Generate hash for content identification"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]