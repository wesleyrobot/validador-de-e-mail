"""
Leitor Inteligente - Versão sem OpenAI
Usa regras inteligentes e regex para normalização
"""

import pandas as pd
import re
from typing import Dict, Optional
import unicodedata

class IntelligentReader:
    """Leitor inteligente com normalização por regras"""
    
    def __init__(self):
        self.enabled = True
        print("✅ Leitor Inteligente iniciado (modo regras)")
    
    def extract_contact_info(self, raw_data: Dict[str, any]) -> Dict[str, any]:
        """
        Extrai e normaliza informações de contato usando regras
        
        Args:
            raw_data: Dados brutos do contato
            
        Returns:
            Dados normalizados
        """
        normalized = {}
        
        for key, value in raw_data.items():
            if not value or (isinstance(value, float) and pd.isna(value)):
                normalized[key] = None
                continue
            
            # Normalizar baseado no tipo de dado
            if 'email' in key.lower():
                normalized[key] = self.normalize_email(str(value))
            elif 'telefone' in key.lower() or 'phone' in key.lower():
                normalized[key] = self.normalize_phone(str(value))
            elif 'nome' in key.lower() or 'name' in key.lower():
                normalized[key] = self.normalize_name(str(value))
            else:
                normalized[key] = self.clean_text(str(value))
        
        return normalized
    
    def normalize_email(self, email: str) -> Optional[str]:
        """Normaliza email"""
        if not email or email == 'nan':
            return None
        
        email = str(email).strip().lower()
        
        # Remover espaços
        email = email.replace(' ', '')
        
        # Correções comuns
        corrections = {
            '..': '.',
            '@@': '@',
            '.@': '@',
            '@.': '@',
        }
        
        for wrong, right in corrections.items():
            email = email.replace(wrong, right)
        
        # Validar formato básico
        if '@' not in email or '.' not in email.split('@')[1]:
            return None
        
        return email
    
    def normalize_phone(self, phone: str) -> Optional[str]:
        """Normaliza telefone brasileiro"""
        if not phone or phone == 'nan':
            return None
        
        # Remover tudo exceto números
        phone = re.sub(r'\D', '', str(phone))
        
        # Se começar com 55 (Brasil)
        if phone.startswith('55'):
            phone = phone[2:]
        
        # Telefone brasileiro: DDD (2) + Número (8 ou 9 dígitos)
        if len(phone) == 11:  # Celular com 9
            return f"+55 {phone[:2]} {phone[2:7]}-{phone[7:]}"
        elif len(phone) == 10:  # Fixo
            return f"+55 {phone[:2]} {phone[2:6]}-{phone[6:]}"
        
        return f"+55 {phone}" if phone else None
    
    def normalize_name(self, name: str) -> Optional[str]:
        """Normaliza nome"""
        if not name or name == 'nan':
            return None
        
        name = self.clean_text(name)
        
        # Capitalizar corretamente
        words = name.split()
        
        # Palavras que devem ficar minúsculas
        lowercase_words = ['de', 'da', 'do', 'dos', 'das', 'e']
        
        capitalized = []
        for i, word in enumerate(words):
            if i > 0 and word.lower() in lowercase_words:
                capitalized.append(word.lower())
            else:
                capitalized.append(word.capitalize())
        
        return ' '.join(capitalized)
    
    def clean_text(self, text: str) -> str:
        """Remove caracteres especiais e normaliza texto"""
        if not text or text == 'nan':
            return ''
        
        text = str(text).strip()
        
        # Remover múltiplos espaços
        text = re.sub(r'\s+', ' ', text)
        
        # Remover caracteres de controle
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        return text
    
    def correct_email(self, email: str) -> Optional[str]:
        """Corrige email usando regras"""
        return self.normalize_email(email)
    
    def categorize_cargo(self, cargo: str) -> str:
        """Categoriza cargo em níveis hierárquicos"""
        if not cargo:
            return "Não classificado"
        
        cargo = cargo.lower()
        
        # C-Level
        c_level = ['ceo', 'cto', 'cfo', 'coo', 'cmo', 'diretor', 'presidente']
        if any(title in cargo for title in c_level):
            return "C-Level / Diretoria"
        
        # Gerência
        gerencia = ['gerente', 'manager', 'coordenador', 'coordinator']
        if any(title in cargo for title in gerencia):
            return "Gerência / Coordenação"
        
        # Supervisão
        supervisao = ['supervisor', 'líder', 'lead']
        if any(title in cargo for title in supervisao):
            return "Supervisão / Liderança"
        
        # Analista
        analista = ['analista', 'analyst', 'especialista', 'specialist']
        if any(title in cargo for title in analista):
            return "Analista / Especialista"
        
        # Assistente
        assistente = ['assistente', 'assistant', 'auxiliar']
        if any(title in cargo for title in assistente):
            return "Assistente / Auxiliar"
        
        # Técnico
        tecnico = ['técnico', 'technician', 'operador']
        if any(title in cargo for title in tecnico):
            return "Técnico / Operacional"
        
        return "Outros"

# Instância global
intelligent_reader = IntelligentReader()
