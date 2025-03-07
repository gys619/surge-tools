import re
import requests
import yaml
from datetime import datetime
from typing import Dict, List, Set
import logging
import os

class ModuleParser:
    def __init__(self):
        self.section_types = {
            'MITM', 'URL-REGEX', 'General', 'Script', 'Host', 'Rule','URL Rewrite','Header Rewrite'
        }
        # 需要合并的特殊配置项
        self.merge_configs = {
            'hostname': {'prefix': '%APPEND%', 'section': 'MITM'},
            'always-real-ip': {'prefix': '%APPEND%', 'section': 'General'},
            'skip-proxy': {'prefix': '%APPEND%', 'section': 'General'},
            'tun-excluded-routes': {'prefix': '%APPEND%', 'section': 'General'}
        }
    
    def parse_config_line(self, line: str, config_type: str) -> List[str]:
        """解析配置行"""
        if not line.startswith(config_type):
            return []
            
        # 移除配置名和等号
        content = line.replace(f"{config_type} = ", "")
        # 移除所有 %APPEND%, %INSERT% 等标记
        content = re.sub(r'%\w+%\s*', '', content)
        # 移除 hostname-disabled = 部分
        content = content.replace('hostname-disabled = ', '')
        # 分割并清理值，移除带减号的值
        return [item.strip() for item in content.split(',') 
                if item.strip() and not item.strip().startswith('-')]
    
    def merge_config_lines(self, lines: List[str], config_type: str, prefix: str) -> str:
        """合并配置行"""
        all_values = set()
        for line in lines:
            values = self.parse_config_line(line, config_type)
            all_values.update(values)
        
        if all_values:
            # 排序并合并所有值，确保没有空值
            values = sorted([v for v in all_values if v])
            if values:
                return f"{config_type} = {prefix} {', '.join(values)}"
        return ""

    def normalize_url_rewrite_rule(self, line: str) -> str:
        """标准化 URL Rewrite 规则，使相似的规则可以被正确比较"""
        # 移除可选的问号 (?), 统一使用 https
        line = line.replace('https?:', 'https:')
        
        # 查找域名部分并标准化格式
        pattern = r'\/\/([\w\.-]+?)/'  # 匹配 // 和域名之间的部分
        match = re.search(pattern, line)
        if match:
            domain = match.group(1)
            # 如果域名中的点号前没有转义符，添加转义符
            if '\\.' not in domain:
                escaped_domain = re.sub(r'\.', r'\.', domain)
                # 确保斜杠也被正确转义
                new_part = f'\\/\\/{escaped_domain}\\/'
                old_part = f'//{domain}/'
                line = line.replace(old_part, new_part)
        
        return line

    def parse_section(self, content: str, module_name: str, exclude_sections: dict) -> Dict[str, List[str]]:
        sections = {}
        current_section = None
        line_number = 0
        config_lines = {config: [] for config in self.merge_configs}
        url_rewrite_rules = set()  # 用于存储标准化的规则
        
        for line in content.splitlines():
            line_number += 1
            line = line.strip()
            
            # 跳过元数据行和注释
            if not line or line.startswith('#'):
                if current_section:  # 如果在段落内，保留注释
                    if current_section not in sections:
                        sections[current_section] = []
                    sections[current_section].append(line)
                continue
            
            # 检查是否应该排除这一行
            if self.should_exclude_line(line, line_number, module_name, exclude_sections):
                logging.info(f"排除行 {line_number}: {line}")
                continue
                
            # 检查是否是段落标记
            if line.startswith('[') and line.endswith(']'):
                # 处理之前段落的配置合并
                if current_section:
                    self._merge_section_configs(sections, current_section, config_lines)
                
                current_section = line[1:-1]
                if current_section not in sections:
                    sections[current_section] = []
                # 重置配置行
                config_lines = {config: [] for config in self.merge_configs}
                continue
                
            if current_section:
                # 检查是否是需要合并的配置
                is_merge_config = False
                for config_type in self.merge_configs:
                    if line.startswith(config_type):
                        if self.merge_configs[config_type]['section'] == current_section:
                            config_lines[config_type].append(line)
                            is_merge_config = True
                            break
                
                # 如果不是需要合并的配置，正常处理
                if not is_merge_config:
                    if current_section not in sections:
                        sections[current_section] = []
                    
                    # 特殊处理 URL Rewrite 段落
                    if current_section == 'URL Rewrite':
                        normalized_line = self.normalize_url_rewrite_rule(line)
                        if normalized_line not in url_rewrite_rules:
                            url_rewrite_rules.add(normalized_line)
                            sections[current_section].append(line)  # 添加原始行
                    else:
                        if line not in sections[current_section]:  # 确保不重复添加
                            sections[current_section].append(line)
        
        # 处理最后一个段落的配置合并
        if current_section:
            self._merge_section_configs(sections, current_section, config_lines)
                
        return sections
    
    def _merge_section_configs(self, sections: Dict[str, List[str]], section: str, config_lines: Dict[str, List[str]]):
        """合并段落内的配置项"""
        for config_type, lines in config_lines.items():
            if lines and self.merge_configs[config_type]['section'] == section:
                merged_line = self.merge_config_lines(
                    lines, 
                    config_type, 
                    self.merge_configs[config_type]['prefix']
                )
                if merged_line:
                    if section not in sections:
                        sections[section] = []
                    # 确保合并的配置行在段落的开始
                    sections[section] = [merged_line] + [
                        l for l in sections.get(section, [])
                        if not any(l.startswith(c) for c in self.merge_configs)
                    ]

    def get_module_name(self, content: str) -> str:
        """从模块内容中获取模块名称"""
        for line in content.splitlines():
            if line.startswith('#!name='):
                name = line.replace('#!name=', '').strip()
                logging.info(f"找到模块名称: {name}")  # 添加日志
                return name
        logging.warning(f"未找到模块名称")  # 添加日志
        return None
    
    def should_exclude_section(self, section: str, module_name: str, exclude_sections: dict) -> bool:
        """判断是否应该排除整个段落"""
        if not exclude_sections or not module_name:
            return False
        
        # 获取该模块需要排除的段落
        module_excludes = exclude_sections.get(module_name, [])
        return section in module_excludes

    def should_exclude(self, line: str, exclude_rules: List[str], section: str = None) -> bool:
        """
        判断是否应该排除某行
        支持:
        1. 完整行匹配
        2. MITM 主机名匹配
        3. 通配符匹配
        """
        # 处理 MITM 段落
        if section == 'MITM' and line.startswith('hostname'):
            hostnames = self.parse_config_line(line, 'hostname')
            # 过滤掉需要排除的主机名
            filtered_hosts = [h for h in hostnames if h not in exclude_rules]
            if filtered_hosts:
                # 重建 hostname 行
                return False, f"hostname = %APPEND% {', '.join(filtered_hosts)}"
            return True, None
            
        # 其他段落的普通匹配
        for exclude in exclude_rules:
            if exclude in line:
                return True, None
                
        return False, None

    def should_exclude_line(self, line: str, line_number: int, module_name: str, exclude_sections: dict) -> bool:
        """判断是否应该排除某一行"""
        if not exclude_sections or not module_name:
            return False
        
        module_excludes = exclude_sections.get(module_name, [])
        for exclude in module_excludes:
            if exclude.startswith('line:'):
                try:
                    # 处理范围格式 (例如: line:16-18)
                    if '-' in exclude:
                        start, end = map(int, exclude.replace('line:', '').split('-'))
                        if start <= line_number <= end:
                            logging.info(f"排除第 {line_number} 行: {line}")  # 添加日志
                            return True
                    # 处理单行格式 (例如: line:17)
                    else:
                        excluded_line = int(exclude.split(':')[1])
                        if line_number == excluded_line:
                            logging.info(f"排除第 {line_number} 行: {line}")  # 添加日志
                            return True
                except ValueError:
                    continue
        return False

    def extract_rules(self, content: str) -> List[str]:
        """从模块中提取规则"""
        rules = []
        in_rule_section = False
        
        for line in content.splitlines():
            line = line.strip()
            
            if line == '[Rule]':
                in_rule_section = True
                continue
            elif line.startswith('['):
                in_rule_section = False
                continue
                
            if in_rule_section and line and not line.startswith('#'):
                rules.append(line)
                
        return rules

class ModuleMerger:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.parser = ModuleParser()
    
    def fetch_module(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.warning(f"获取模块失败: {url}, 错误: {str(e)}")
            return ""
    
    def merge_module(self, module_name: str) -> Dict:
        module_config = self.config['modules']['sources'][module_name]
        sections = {}
        all_hostnames = set()
        success = False
        
        # 检查所有配置参数
        # 1. 检查 exclude_rules
        exclude_rules = set(module_config.get('exclude_rules', []))
        if exclude_rules and not any(exclude_rules):
            logging.warning(f"模块 {module_name} 的 exclude_rules 配置为空，将不进行排除")
            exclude_rules = set()
        
        # 2. 检查 exclude_sections
        exclude_sections = module_config.get('exclude_sections', {})
        if exclude_sections and not any(exclude_sections.values()):
            logging.warning(f"模块 {module_name} 的 exclude_sections 配置为空，将不进行排除")
            exclude_sections = {}
        
        # 3. 检查 section_preference
        section_preference = module_config.get('section_preference', [])
        if section_preference and not any(section_preference):
            logging.warning(f"模块 {module_name} 的 section_preference 配置为空，将使用默认顺序")
            section_preference = []
        
        # 4. 检查 exclude_module_sets
        exclude_module_sets = module_config.get('exclude_module_sets', [])
        if exclude_module_sets and not any(exclude_module_sets):
            logging.warning(f"模块 {module_name} 的 exclude_module_sets 配置为空，将不排除任何模块")
            exclude_module_sets = []
            
        # 获取需要排除的模块内容
        excluded_content = set()
        for exclude_url in exclude_module_sets:
            content = self.fetch_module(exclude_url)
            if content:
                # 解析需要排除的内容
                parsed_sections = self.parser.parse_section(content, None, {})
                for section in parsed_sections.values():
                    excluded_content.update(section)
        
        # 合并模块
        for url in module_config['urls']:
            content = self.fetch_module(url)
            if content:
                success = True
                current_module_name = self.parser.get_module_name(content)
                logging.info(f"\n处理模块: {url}")
                
                parsed_sections = self.parser.parse_section(
                    content,
                    current_module_name,
                    exclude_sections
                )
                
                # 合并各个段落
                for section, lines in parsed_sections.items():
                    if self.parser.should_exclude_section(section, current_module_name, exclude_sections):
                        logging.info(f"排除段落: {section} 从模块: {current_module_name}")
                        continue
                        
                    if section not in sections:
                        sections[section] = []
                    
                    # 处理每一行
                    for line in lines:
                        # 检查是否在排除的模块内容中
                        if line in excluded_content:
                            logging.info(f"排除来自其他模块的内容: {line}")
                            continue
                            
                        should_exclude, new_line = self.parser.should_exclude(
                            line, 
                            exclude_rules, 
                            section
                        )
                        if not should_exclude:
                            if section == 'MITM' and line.startswith('hostname'):
                                hostnames = self.parser.parse_config_line(line, 'hostname')
                                all_hostnames.update(hostnames)
                            elif new_line and new_line not in sections[section]:
                                sections[section].append(new_line)
                            elif not new_line and line not in sections[section]:
                                sections[section].append(line)
        
        # 移除空段落
        sections = {k: v for k, v in sections.items() if v}
        
        # 如果有收集到 hostname，添加到 MITM 段落
        if all_hostnames:
            if 'MITM' not in sections:
                sections['MITM'] = []
            sections['MITM'] = [f"hostname = %APPEND% {', '.join(sorted(all_hostnames))}"]
        
        # 如果所有段落都为空，返回 None
        if not any(sections.values()):
            logging.warning(f"模块 {module_name} 合并后为空")
            return None
        
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
        
        # Debugging: print the type and content of the result
        result = {
            'metadata': {
                'name': module_config['name'],
                'desc': module_config['desc'],
                'author': module_config['author'],
                'repo': module_config['repo'],
                'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'sections': ordered_sections
        }
        
        print("merge_module result type:", type(result))
        print("merge_module result content:", result)

        return result

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
            
            # 处理注释和规则，确保注释紧跟在它们所描述的规则之前
            previous_line_was_comment = False
            for line in rules:
                if line.startswith('#'):
                    lines.append(line)
                    previous_line_was_comment = True
                else:
                    if previous_line_was_comment:
                        # 如果前一行是注释，直接添加规则
                        lines.append(line)
                    else:
                        # 如果前一行不是注释，确保规则和注释之间有空行
                        lines.append("")
                        lines.append(line)
                    previous_line_was_comment = False
            
            lines.append("")  # 段落之间添加空行
        
        return "\n".join(lines)

    def remove_unnecessary_comments(self, content: str) -> str:
        """移除无用的注释"""
        lines = content.split('\n')
        filtered_lines = [line for line in lines if not line.strip().startswith('#')]
        return '\n'.join(filtered_lines)

    def save_merged_content(self, file_path, content):
        """
        保存合并后的内容，但如果只有时间戳更新则不保存
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                existing_content = file.read()
                
                # 将现有内容和新内容按行分割
                existing_lines = existing_content.splitlines()
                new_lines = content.splitlines()
                
                # 如果行数不同，说明有实质性更新
                if len(existing_lines) != len(new_lines):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logging.info(f"文件已更新: {file_path}")
                    return
                
                # 比较除了时间戳之外的所有行
                has_real_changes = False
                for old_line, new_line in zip(existing_lines, new_lines):
                    # 跳过时间戳行的比较
                    if old_line.startswith('#!updated='):
                        continue
                    if old_line != new_line:
                        has_real_changes = True
                        break
                
                if has_real_changes:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logging.info(f"文件已更新: {file_path}")
                else:
                    logging.info(f"仅时间戳变化，不更新文件: {file_path}")
                
        except FileNotFoundError:
            # 如果文件不存在，创建新文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"创建新文件: {file_path}") 