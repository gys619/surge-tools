import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urlparse

@dataclass
class Rule:
    type: str
    content: str
    original: str

class RuleParser:
    def __init__(self):
        self.rule_types = {
            'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD',
            'IP-CIDR', 'IP-CIDR6', 'URL-REGEX'
        }
        
    def parse_line(self, line: str) -> Rule:
        line = line.strip()
        if not line or line.startswith('#'):
            return None
            
        parts = line.split(',')
        if len(parts) < 2:
            return None
            
        rule_type = parts[0].strip()
        if rule_type not in self.rule_types:
            return None
            
        content = parts[1].strip()
        return Rule(type=rule_type, content=content, original=line)
        
    def is_subdomain(self, domain: str, potential_parent: str) -> bool:
        if domain == potential_parent:
            return False
        return domain.endswith(f".{potential_parent}")
        
    def should_exclude(self, rule: Rule, exclude_rules: List[str]) -> bool:
        for exclude in exclude_rules:
            if rule.content == exclude:
                return True
            if rule.type == 'DOMAIN' and self.is_subdomain(rule.content, exclude):
                return True
        return False 