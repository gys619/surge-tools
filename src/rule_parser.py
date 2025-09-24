import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urlparse

@dataclass(frozen=True)
class Rule:
    type: str
    content: str
    original: str

    def __hash__(self):
        return hash((self.type, self.content))
    
    def __eq__(self, other):
        if not isinstance(other, Rule):
            return False
        return self.type == other.type and self.content == other.content

class RuleParser:
    def __init__(self):
        self.rule_types = {
            'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD',
            'IP-CIDR', 'IP-CIDR6', 'IP-ASN', 'URL-REGEX'
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
    
    def parse_exclude_rule(self, exclude_rule: str) -> tuple:
        """解析排除规则
        支持格式:
        1. 完整规则: DOMAIN,example.com
        2. 仅内容: example.com
        3. 类型指定: DOMAIN-SUFFIX:*.example.com
        4. 通配符: *.example.com
        """
        if ',' in exclude_rule:  # 完整规则
            rule_type, content = exclude_rule.split(',', 1)
            return rule_type.strip(), content.strip()
        elif ':' in exclude_rule:  # 类型指定
            rule_type, content = exclude_rule.split(':', 1)
            return rule_type.strip(), content.strip()
        else:  # 仅内容或通配符
            content = exclude_rule.strip()
            if content.startswith('*.'):
                return 'DOMAIN-SUFFIX', content[2:]
            return None, content
        
    def should_exclude(self, rule: Rule, exclude_rules) -> bool:
        for exclude in exclude_rules:
            exclude_type, exclude_content = self.parse_exclude_rule(exclude)
            
            # 如果指定了类型，必须匹配类型
            if exclude_type and exclude_type != rule.type:
                continue
                
            # 处理通配符
            if exclude_content.startswith('*.'):
                if rule.type in ['DOMAIN', 'DOMAIN-SUFFIX']:
                    base_domain = exclude_content[2:]
                    if rule.content.endswith(base_domain):
                        return True
                continue
            
            # 完全匹配
            if rule.content == exclude_content:
                return True
            
            # 域名嵌套关系
            if rule.type == 'DOMAIN' and self.is_subdomain(rule.content, exclude_content):
                return True
                
            # DOMAIN-SUFFIX 特殊处理
            if rule.type == 'DOMAIN-SUFFIX' and exclude_content.endswith(rule.content):
                return True
        
        return False 