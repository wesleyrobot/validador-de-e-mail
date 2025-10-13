"""
Validador de Email com verificação DNS/MX
"""

import re
import dns.resolver
from typing import Dict, Tuple
from email_validator import validate_email, EmailNotValidError

class EmailValidatorDNS:
    """Validador avançado de emails com DNS/MX"""
    
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 3
        self.resolver.lifetime = 3
    
    def validate(self, email: str) -> Dict[str, any]:
        """
        Valida email completamente
        
        Returns:
            {
                'valid': bool,
                'email': str (normalizado),
                'status': str,
                'reason': str
            }
        """
        if not email or not isinstance(email, str):
            return {
                'valid': False,
                'email': email,
                'status': 'invalid',
                'reason': 'Email vazio ou inválido'
            }
        
        email = email.strip().lower()
        
        # 1. Validação de formato
        if not self._is_valid_format(email):
            return {
                'valid': False,
                'email': email,
                'status': 'invalid',
                'reason': 'Formato inválido'
            }
        
        # 2. Validação com email-validator
        try:
            validated = validate_email(email, check_deliverability=False)
            email = validated.normalized
        except EmailNotValidError as e:
            return {
                'valid': False,
                'email': email,
                'status': 'invalid',
                'reason': str(e)
            }
        
        # 3. Verificação DNS/MX
        domain = email.split('@')[1]
        has_mx = self._check_mx_record(domain)
        
        if has_mx:
            return {
                'valid': True,
                'email': email,
                'status': 'valid',
                'reason': 'Email válido com MX'
            }
        else:
            return {
                'valid': False,
                'email': email,
                'status': 'no_mx',
                'reason': 'Domínio sem registro MX'
            }
    
    def _is_valid_format(self, email: str) -> bool:
        """Valida formato básico do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _check_mx_record(self, domain: str) -> bool:
        """Verifica se domínio tem registro MX"""
        try:
            mx_records = self.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False
        except Exception:
            return False

# Instância global
email_validator = EmailValidatorDNS()
