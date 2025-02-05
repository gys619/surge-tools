import requests
import yaml
from datetime import datetime
from typing import Dict, List, Set
from .rule_parser import RuleParser, Rule
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RuleMerger:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.parser = RuleParser()
        
    def fetch_rules(self, url: str) -> List[str]:
        try:
            response = requests.get(url, timeout=10)  # 添加超时设置
            response.raise_for_status()
            return response.text.splitlines()
        except requests.exceptions.RequestException as e:
            logging.warning(f"获取规则失败: {url}, 错误: {str(e)}")
            return []
        
    def merge_rules(self, rule_set_name: str) -> Dict:
        rule_config = self.config['rules']['sources'][rule_set_name]
        rules: Dict[str, Set[Rule]] = {
            'DOMAIN': set(),
            'DOMAIN-SUFFIX': set(),
            'DOMAIN-KEYWORD': set(),
            'IP-CIDR': set(),
            'IP-CIDR6': set(),
            'URL-REGEX': set()
        }
        
        # 获取排除规则
        exclude_rules = set(rule_config.get('exclude_rules', []))
        
        # 获取需要排除的规则集
        for exclude_url in rule_config.get('exclude_rule_sets', []):
            exclude_lines = self.fetch_rules(exclude_url)
            for line in exclude_lines:
                rule = self.parser.parse_line(line)
                if rule:
                    exclude_rules.add(rule.content)
        
        # 合并规则
        success = False  # 标记是否有成功获取的规则
        for url in rule_config['urls']:
            lines = self.fetch_rules(url)
            if lines:  # 如果获取到规则
                success = True
                for line in lines:
                    rule = self.parser.parse_line(line)
                    if rule and not self.parser.should_exclude(rule, exclude_rules):
                        rules[rule.type].add(rule)
        
        # 如果没有成功获取任何规则，返回 None
        if not success:
            logging.warning(f"规则集 {rule_set_name} 所有源获取失败")
            return None
            
        # 如果规则为空，返回 None
        total_rules = sum(len(rules[rule_type]) for rule_type in rules)
        if total_rules == 0:
            logging.warning(f"规则集 {rule_set_name} 合并后为空")
            return None
        
        return {
            'metadata': {
                'name': rule_config['name'],
                'author': rule_config['author'],
                'repo': rule_config['repo'],
                'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'description': rule_config['description'],
            },
            'rules': rules
        } 