import re
import requests
import yaml
from datetime import datetime
from typing import Dict, List, Set

class ModuleParser:
    def __init__(self):
        self.section_types = {
            'MITM', 'URL-REGEX', 'General', 'Script', 'Host'
        }
    
    def parse_section(self, content: str) -> Dict[str, List[str]]:
        sections = {}
        current_section = None
        
        for line in content.splitlines():
            line = line.strip()
            # 跳过元数据行和注释
            if not line or line.startswith('#'):
                continue
                
            # 检查是否是段落标记
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                sections[current_section] = []
                continue
                
            if current_section:
                sections[current_section].append(line)
                
        return sections
    
    def should_exclude(self, line: str, exclude_rules: List[str]) -> bool:
        for exclude in exclude_rules:
            if exclude in line:
                return True
        return False

class ModuleMerger:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.parser = ModuleParser()
    
    def fetch_module(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    
    def merge_modules(self, module_name: str) -> Dict:
        module_config = self.config['modules']['sources'][module_name]
        sections: Dict[str, Set[str]] = {}
        
        # 获取排除规则
        exclude_rules = set(module_config.get('exclude_rules', []))
        
        # 获取需要排除的模块集
        for exclude_url in module_config.get('exclude_module_sets', []):
            exclude_content = self.fetch_module(exclude_url)
            exclude_sections = self.parser.parse_section(exclude_content)
            for section_content in exclude_sections.values():
                exclude_rules.update(section_content)
        
        # 合并模块
        for url in module_config['urls']:
            content = self.fetch_module(url)
            parsed_sections = self.parser.parse_section(content)
            
            for section, lines in parsed_sections.items():
                if section not in sections:
                    sections[section] = set()
                
                for line in lines:
                    if not self.parser.should_exclude(line, exclude_rules):
                        sections[section].add(line)
        
        # 按照优先级排序段落
        section_preference = module_config.get('section_preference', [])
        ordered_sections = {}
        
        # 首先添加有优先级的段落
        for section in section_preference:
            if section in sections:
                ordered_sections[section] = sections[section]
        
        # 然后添加其他段落
        for section in sections:
            if section not in ordered_sections:
                ordered_sections[section] = sections[section]
        
        return {
            'metadata': {
                'name': module_config['name'],
                'desc': module_config['desc'],
                'author': module_config['author'],
                'repo': module_config['repo'],
                'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'sections': ordered_sections
        }

    def format_module_content(self, merged_data: Dict) -> str:
        """格式化模块内容"""
        lines = []
        
        # 添加新的元数据
        meta = merged_data['metadata']
        lines.extend([
            f"#!name={meta['name']}",
            f"#!desc={meta['desc']}",
            f"#!author={meta['author']}",
            f"#!repo={meta['repo']}",
            f"#!updated={meta['updated']}",
            ""
        ])
        
        # 添加各个段落的内容
        for section, rules in merged_data['sections'].items():
            lines.append(f"[{section}]")
            lines.extend(sorted(rules))  # 对规则进行排序
            lines.append("")  # 段落之间添加空行
        
        return "\n".join(lines) 