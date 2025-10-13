"""
Processador de Contatos - Validação DNS/MX, Normalização e Categorização
Requisitos: pip install dnspython email-validator phonenumbers rapidfuzz
"""

import pandas as pd
import dns.resolver
import re
from email_validator import validate_email, EmailNotValidError
from typing import Dict, List, Any, Optional
import time

class ContactProcessor:
    def __init__(self, dns_timeout: int = 3, cache_enabled: bool = True):
        self.dns_timeout = dns_timeout
        self.cache_enabled = cache_enabled
        self.domain_cache = {}  # Cache simples em memória
        
        # Configurar resolver DNS
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = dns_timeout
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza nomes de colunas e dados básicos
        """
        # Padronizar nomes de colunas
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        
        # Mapear nomes comuns de colunas
        column_mapping = {
            "nome": "nome",
            "name": "nome",
            "email": "email",
            "e-mail": "email",
            "email1": "email",  # ADICIONADO
            "email2": "email_secundario",  # ADICIONADO
            "telefone": "telefone",
            "telefone1": "telefone",  # ADICIONADO
            "telefone2": "telefone_secundario",  # ADICIONADO
            "phone": "telefone",
            "empresa": "empresa",
            "company": "empresa",
            "cargo": "cargo",
            "position": "cargo",
            "role": "cargo",
            "observações": "observacoes",
            "notes": "observacoes",
            "obs": "observacoes",
            "país": "pais",
            "pais": "pais",
            "estado": "pais",  # ADICIONADO - usar estado como país
            "country": "pais",
            "cidade": "cidade",  # ADICIONADO
            "cpf/cnpj": "documento"  # ADICIONADO
        }
        
        df = df.rename(columns=column_mapping)
        
        # Garantir colunas essenciais existem
        required_cols = ["nome", "email", "telefone", "empresa", "cargo", "observacoes"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        
        # Limpar espaços
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def validate_email_syntax(self, email: str) -> bool:
        """
        Valida sintaxe do e-mail
        """
        if not email or pd.isna(email):
            return False
        
        try:
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
    
    def check_domain_mx_a(self, domain: str) -> Dict[str, Any]:
        """
        Verifica registros MX e A do domínio via DNS
        """
        # Usar cache se habilitado
        if self.cache_enabled and domain in self.domain_cache:
            return self.domain_cache[domain]
        
        resultado = {
            "mx": [],
            "a": [],
            "domain_valid": False,
            "check_type": None,
            "error": None
        }
        
        try:
            # Tentar registros MX primeiro
            try:
                mx_answers = self.resolver.resolve(domain, 'MX')
                resultado["mx"] = [str(r.exchange).rstrip('.') for r in mx_answers]
                resultado["domain_valid"] = len(resultado["mx"]) > 0
                resultado["check_type"] = "MX"
            except dns.resolver.NoAnswer:
                # Se não há MX, tentar registro A
                try:
                    a_answers = self.resolver.resolve(domain, 'A')
                    resultado["a"] = [str(r) for r in a_answers]
                    resultado["domain_valid"] = len(resultado["a"]) > 0
                    resultado["check_type"] = "A"
                except Exception as e:
                    resultado["error"] = f"No MX or A records: {str(e)}"
            
        except dns.resolver.NXDOMAIN:
            resultado["error"] = "Domain does not exist"
        except dns.resolver.Timeout:
            resultado["error"] = "DNS query timeout"
        except Exception as e:
            resultado["error"] = str(e)
        
        # Cachear resultado
        if self.cache_enabled:
            self.domain_cache[domain] = resultado
        
        return resultado
    
    def validate_email_full(self, email: str) -> Dict[str, Any]:
        """
        Validação completa: sintaxe + domínio DNS/MX
        """
        result = {
            "email": email,
            "syntax_valid": False,
            "domain_valid": False,
            "mx_records": [],
            "a_records": [],
            "check_type": None,
            "validation_status": "invalid",
            "error": None
        }
        
        # Validar sintaxe
        if not self.validate_email_syntax(email):
            result["error"] = "Invalid email syntax"
            return result
        
        result["syntax_valid"] = True
        
        # Extrair domínio
        try:
            domain = email.split("@")[1].lower()
        except IndexError:
            result["error"] = "Cannot extract domain"
            return result
        
        # Validar domínio
        domain_check = self.check_domain_mx_a(domain)
        result["domain_valid"] = domain_check["domain_valid"]
        result["mx_records"] = domain_check["mx"]
        result["a_records"] = domain_check["a"]
        result["check_type"] = domain_check["check_type"]
        result["error"] = domain_check["error"]
        
        # Status final
        if result["syntax_valid"] and result["domain_valid"]:
            result["validation_status"] = "valid"
        elif result["syntax_valid"] and not result["domain_valid"]:
            result["validation_status"] = "syntax_only"
        else:
            result["validation_status"] = "invalid"
        
        return result
    
    def normalize_phone(self, phone: str) -> str:
        """
        Normaliza telefone (formato básico)
        Para normalização avançada, use: import phonenumbers
        """
        if not phone or pd.isna(phone):
            return ""
        
        # Remover caracteres não numéricos exceto +
        phone = re.sub(r'[^\d+]', '', str(phone))
        return phone
    
    def categorize_by_keywords(self, text: str, keywords_map: Dict[str, List[str]]) -> Optional[str]:
        """
        Categoriza texto baseado em palavras-chave
        """
        if not text or pd.isna(text):
            return None
        
        text_lower = str(text).lower()
        
        for category, keywords in keywords_map.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return None
    
    def process_contacts(self, df: pd.DataFrame, job_id: str = None, jobs_dict: dict = None) -> List[Dict[str, Any]]:
        """
        Processa DataFrame completo de contatos
        """
        # Normalizar DataFrame
        df = self.normalize_dataframe(df)
        
        total = len(df)
        results = []
        
        # Palavras-chave para categorização automática
        cargo_categories = {
            "executivo": ["ceo", "diretor", "presidente", "vp", "vice-presidente"],
            "gerencia": ["gerente", "manager", "coordenador", "supervisor"],
            "vendas": ["vendas", "sales", "comercial", "account"],
            "marketing": ["marketing", "publicidade", "comunicação"],
            "ti": ["ti", "tecnologia", "desenvolvedor", "programador", "engenheiro"],
            "rh": ["rh", "recursos humanos", "recrutador"],
            "financeiro": ["financeiro", "contabilidade", "controller"]
        }
        
        for idx, row in df.iterrows():
            # Atualizar progresso
            if job_id and jobs_dict:
                progress = int(10 + (idx / total) * 85)
                jobs_dict[job_id]["progress"] = progress
            
            # Dados básicos
            contact = {
                "id": idx + 1,
                "nome": str(row.get("nome", "")).strip(),
                "email": str(row.get("email", "")).strip().lower(),
                "telefone": self.normalize_phone(row.get("telefone", "")),
                "empresa": str(row.get("empresa", "")).strip(),
                "cargo": str(row.get("cargo", "")).strip(),
                "pais": str(row.get("pais", "")).strip() if "pais" in row else "",
                "observacoes": str(row.get("observacoes", "")).strip()
            }
            
            # Validação de e-mail
            email_validation = self.validate_email_full(contact["email"])
            contact.update({
                "email_syntax_valid": email_validation["syntax_valid"],
                "email_domain_valid": email_validation["domain_valid"],
                "email_mx_records": ", ".join(email_validation["mx_records"][:2]),  # Primeiros 2 MX
                "email_validation_status": email_validation["validation_status"],
                "email_validation_error": email_validation["error"]
            })
            
            # Categorização automática por cargo
            cargo_category = self.categorize_by_keywords(
                contact["cargo"],
                cargo_categories
            )
            contact["categoria_cargo"] = cargo_category or "outros"
            
            results.append(contact)
            
            # Rate limiting para não sobrecarregar DNS
            if idx % 50 == 0:
                time.sleep(0.1)
        
        return results


def categorize_by_field(data: List[Dict], by: str, rules: Optional[Dict] = None) -> List[Dict]:
    """
    Reorganiza dados por campo específico
    """
    for item in data:
        if by == "cargo":
            # Já categorizado em categoria_cargo
            pass
        elif by == "empresa":
            item["categoria"] = item.get("empresa", "sem_empresa")
        elif by == "pais":
            item["categoria"] = item.get("pais", "sem_pais")
        elif by == "custom" and rules:
            # Aplicar regras customizadas
            for key, value in rules.items():
                if key in item and str(item[key]).lower() in str(value).lower():
                    item["categoria"] = value
    
    return data