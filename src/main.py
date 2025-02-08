import os
from .rule_merger import RuleMerger
from .module_merger import ModuleMerger
import logging
import hashlib
from datetime import datetime

def is_valid_domain(domain: str) -> bool:
    """验证域名格式是否有效"""
    if not domain or len(domain) > 255:
        return False
    if domain.startswith('.') or domain.endswith('.'):
        return False
    allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._')
    return all(c in allowed for c in domain)

def is_subdomain(subdomain: str, domain: str) -> bool:
    """检查是否为子域名"""
    if not (is_valid_domain(subdomain) and is_valid_domain(domain)):
        return False
    return subdomain.endswith(f'.{domain}') or subdomain == domain

def optimize_rules(rules: dict) -> dict:
    """优化规则集，去除冗余规则"""
    optimized = {rule_type: set() for rule_type in rules}
    
    # 预处理函数：将规则分割为(policy, domain)元组
    def preprocess_rules(rule_set):
        if not rule_set:
            return set()
        return {tuple(r.split(',', 1)) for r in rule_set}
    
    # 1. 预处理所有域名相关规则
    domains = preprocess_rules(rules.get('DOMAIN', []))
    domain_suffixes = preprocess_rules(rules.get('DOMAIN-SUFFIX', []))
    domain_keywords = preprocess_rules(rules.get('DOMAIN-KEYWORD', []))
    domain_wildcards = preprocess_rules(rules.get('DOMAIN-WILDCARD', []))
    
    # 创建域名到策略的映射，避免重复分割
    domain_map = {domain: policy for policy, domain in domains}
    suffix_map = {suffix: policy for policy, suffix in domain_suffixes}
    
    # 2. 移除无效域名（使用已分割的数据）
    domains = {(policy, domain) for policy, domain in domains if is_valid_domain(domain)}
    domain_suffixes = {(policy, suffix) for policy, suffix in domain_suffixes if is_valid_domain(suffix)}
    
    # 3. 优化 DOMAIN 和 DOMAIN-SUFFIX 的关系
    # 创建后缀树来加速查找
    suffix_tree = set()
    for _, suffix in domain_suffixes:
        parts = suffix.split('.')
        for i in range(len(parts)):
            suffix_tree.add('.'.join(parts[i:]))
    
    # 过滤被后缀规则覆盖的域名
    filtered_domains = set()
    for policy, domain in domains:
        parts = domain.split('.')
        covered = False
        for i in range(len(parts)):
            if '.'.join(parts[i:]) in suffix_tree:
                covered = True
                break
        if not covered:
            filtered_domains.add((policy, domain))
    
    # 4. 优化 DOMAIN-KEYWORD（使用集合操作）
    filtered_keywords = set()
    for policy, keyword in domain_keywords:
        if not any(keyword in domain for _, domain in domains) and \
           not any(keyword in suffix for _, suffix in domain_suffixes):
            filtered_keywords.add((policy, keyword))
    
    # 5. 优化 DOMAIN-WILDCARD
    filtered_wildcards = set()
    for policy, wildcard in domain_wildcards:
        clean_wildcard = wildcard.replace('*', '').replace('.', '')
        if not any(clean_wildcard in domain.replace('.', '') for _, domain in domains):
            filtered_wildcards.add((policy, wildcard))
    
    # 6. 处理 IP 规则
    ip_cidrs = set(rules.get('IP-CIDR', []))
    ip_cidrs6 = set(rules.get('IP-CIDR6', []))
    
    # 使用集合推导式处理 IP 规则
    ipv6_rules = {ip for ip in ip_cidrs if ':' in ip.split(',')[1]}
    ip_cidrs = ip_cidrs - ipv6_rules
    ip_cidrs6.update(ipv6_rules)
    
    # 7. 重建规则字符串并更新优化后的规则集
    def rebuild_rules(rule_set):
        return {f"{policy},{value}" for policy, value in rule_set}
    
    if filtered_domains:
        optimized['DOMAIN'] = sorted(rebuild_rules(filtered_domains))
    if domain_suffixes:
        optimized['DOMAIN-SUFFIX'] = sorted(rebuild_rules(domain_suffixes))
    if filtered_keywords:
        optimized['DOMAIN-KEYWORD'] = sorted(rebuild_rules(filtered_keywords))
    if filtered_wildcards:
        optimized['DOMAIN-WILDCARD'] = sorted(rebuild_rules(filtered_wildcards))
    if ip_cidrs:
        optimized['IP-CIDR'] = sorted(ip_cidrs)
    if ip_cidrs6:
        optimized['IP-CIDR6'] = sorted(ip_cidrs6)
    
    # 8. 复制其他类型的规则
    for rule_type in rules:
        if rule_type not in optimized:
            optimized[rule_type] = sorted(set(rules[rule_type]))
    
    return optimized

def get_content_hash(rules: dict) -> str:
    """计算规则内容的哈希值"""
    # 将规则转换为稳定的字符串格式进行哈希
    content = []
    for rule_type in sorted(rules.keys()):
        content.append(f"{rule_type}:")
        for rule in sorted(rules[rule_type]):
            content.append(rule)
    
    content_str = '\n'.join(content)
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()

def generate_rule_file(merged_data: dict, output_path: str):
    # 在写入之前优化规则
    merged_data['rules'] = optimize_rules(merged_data['rules'])
    
    # 计算新内容的哈希值
    new_hash = get_content_hash(merged_data['rules'])
    
    # 检查现有文件的哈希值
    old_hash = None
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('# HASH: '):
                    old_hash = line.strip().split(': ')[1]
                    break
    
    # 如果哈希值相同，说明内容没有变化，直接返回
    if old_hash and old_hash == new_hash:
        return False
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入元数据
        meta = merged_data['metadata']
        f.write(f"# NAME: {meta['name']}\n")
        f.write(f"# AUTHOR: {meta['author']}\n")
        f.write(f"# REPO: {meta['repo']}\n")
        # 只在内容变化时更新时间戳
        f.write(f"# UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# DESCRIPTION: {meta['description']}\n")
        # 写入内容哈希值
        f.write(f"# HASH: {new_hash}\n")
        
        # 写入统计信息
        rules = merged_data['rules']
        total = sum(len(rules[rule_type]) for rule_type in rules)
        for rule_type in rules:
            f.write(f"# {rule_type}: {len(rules[rule_type])}\n")
        f.write(f"# TOTAL: {total}\n\n")
        
        # 写入规则
        for rule_type in rules:
            for rule in rules[rule_type]:
                f.write(f"{rule}\n")
    
    return True

def generate_module_file(merged_data: dict, module_merger: ModuleMerger, output_path: str):
    """生成模块文件"""
    # 获取新的模块内容
    module_content = module_merger.format_module_content(merged_data)
    
    # 提取和规范化内容（移除时间戳和哈希值行，并确保空行一致性）
    def normalize_content(content):
        lines = []
        for line in content.split('\n'):
            # 跳过时间戳、哈希值和空行
            if line.startswith('#!updated=') or line.startswith('#!HASH=') or not line.strip():
                continue
            lines.append(line)
        return '\n'.join(lines)
    
    # 获取规范化后的新内容
    new_content = normalize_content(module_content)
    new_hash = hashlib.md5(new_content.encode('utf-8')).hexdigest()
    
    # 检查现有文件的内容
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            old_content = normalize_content(f.read())
            if new_content == old_content:
                return False
    
    # 内容有变化，重新组织文件内容
    lines = []
    header_lines = []
    content_lines = []
    
    # 分离头部注释和内容
    for line in module_content.split('\n'):
        if line.startswith('#!'):
            if not line.startswith('#!updated=') and not line.startswith('#!HASH='):
                header_lines.append(line)
        else:
            if line.strip():  # 只添加非空行
                content_lines.append(line)
    
    # 组合最终内容
    lines.extend(header_lines)
    lines.append(f'#!updated={datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'#!HASH={new_hash}')
    lines.append('')  # 添加一个空行分隔头部和内容
    lines.extend(content_lines)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return True

def main():
    merger = RuleMerger('config/config.yaml')
    
    # 确保输出目录存在
    os.makedirs(merger.config['rules']['output_dir'], exist_ok=True)
    
    # 处理每个规则集
    for rule_set_name in merger.config['rules']['sources']:
        merged_data = merger.merge_rules(rule_set_name)
        if merged_data:  # 只有在成功获取规则时才生成文件
            output_path = os.path.join(
                merger.config['rules']['output_dir'],
                f"{rule_set_name}.list"
            )
            if generate_rule_file(merged_data, output_path):
                logging.info(f"规则文件已更新: {rule_set_name}.list")
            else:
                logging.info(f"规则文件无变化: {rule_set_name}.list")
    
    # 处理模块
    if 'modules' in merger.config:
        module_merger = ModuleMerger('config/config.yaml')
        os.makedirs(module_merger.config['modules']['output_dir'], exist_ok=True)
        
        for module_name in module_merger.config['modules']['sources']:
            merged_data = module_merger.merge_module(module_name)
            if merged_data:  # 只有在成功获取模块时才生成文件
                output_path = os.path.join(
                    module_merger.config['modules']['output_dir'],
                    f"{module_name}.sgmodule"
                )
                if generate_module_file(merged_data, module_merger, output_path):
                    logging.info(f"模块文件已更新: {module_name}.sgmodule")
                else:
                    logging.info(f"模块文件无变化: {module_name}.sgmodule")

    # Example configuration
    example_config = {
        "modules": ["modules/advertising_mitm.sgmodule", "modules/AppRemoveAds.sgmodule"],
        "output": "merged_output.sgmodule"
    }
    print("Example configuration:", example_config)

if __name__ == "__main__":
    main() 