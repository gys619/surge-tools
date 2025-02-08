import os
import requests
import yaml
from datetime import datetime
from typing import Dict, List, Set
from src.rule_parser import RuleParser, Rule
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
            logging.info(f"开始下载规则: {url}")
            # 增加超时时间到30秒，移除代理设置
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            lines = response.text.splitlines()
            logging.info(f"规则下载成功: {url}, 共 {len(lines)} 行")
            return lines
        except requests.exceptions.RequestException as e:
            logging.warning(f"获取规则失败: {url}, 错误: {str(e)}")
            return []
        
    def merge_rules(self, rule_set_name: str) -> Dict:
        logging.info(f"开始处理规则集: {rule_set_name}")
        rule_config = self.config['rules']['sources'][rule_set_name]
        rules: Dict[str, Set[str]] = {  # 使用 Set 而不是 List 来存储规则
            'DOMAIN': set(),
            'DOMAIN-SUFFIX': set(),
            'DOMAIN-KEYWORD': set(),
            'IP-CIDR': set(),
            'IP-CIDR6': set(),
            'URL-REGEX': set()
        }
        
        # 获取排除规则，过滤掉空值
        exclude_rules = set(rule for rule in rule_config.get('exclude_rules', []) if rule)
        
        # 获取需要排除的规则集，过滤掉空值
        for exclude_url in (url for url in rule_config.get('exclude_rule_sets', []) if url):
            logging.info(f"获取排除规则集: {exclude_url}")
            exclude_lines = self.fetch_rules(exclude_url)
            for line in exclude_lines:
                rule = self.parser.parse_line(line)
                if rule:
                    exclude_rules.add(rule.content)
        
        # 合并规则
        success = False
        for url in rule_config['urls']:
            logging.info(f"正在获取规则: {url}")
            lines = self.fetch_rules(url)
            if lines:
                success = True
                logging.info(f"成功获取规则，共 {len(lines)} 行")
                for line in lines:
                    rule = self.parser.parse_line(line)
                    if rule and not self.parser.should_exclude(rule, exclude_rules):
                        rules[rule.type].add(rule.original)  # 存储原始行，而不是 Rule 对象
            else:
                logging.warning(f"获取规则失败: {url}")
        
        if not success:
            logging.warning(f"规则集 {rule_set_name} 所有源获取失败")
            return None
            
        # 如果规则为空，返回 None
        total_rules = sum(len(rules[rule_type]) for rule_type in rules)
        if total_rules == 0:
            logging.warning(f"规则集 {rule_set_name} 合并后为空")
            return None
        
        # 按照优先级排序规则
        rule_preference = rule_config.get('rule_preference', [])
        ordered_rules = {}
        
        # 首先添加有优先级的规则类型
        for rule_type in rule_preference:
            if rule_type in rules and rules[rule_type]:
                ordered_rules[rule_type] = sorted(rules[rule_type])  # 对规则进行排序
        
        # 然后添加其他规则类型
        for rule_type in rules:
            if rule_type not in ordered_rules and rules[rule_type]:
                ordered_rules[rule_type] = sorted(rules[rule_type])
        
        return {
            'metadata': {
                'name': rule_config['name'],
                'author': rule_config['author'],
                'repo': rule_config['repo'],
                'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'description': rule_config['description'],
            },
            'rules': ordered_rules
        } 