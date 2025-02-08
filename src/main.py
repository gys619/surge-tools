import os
from .rule_merger import RuleMerger
from .module_merger import ModuleMerger
import logging

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
    
    # 1. 处理域名相关规则
    domains = set(rules.get('DOMAIN', []))
    domain_suffixes = set(rules.get('DOMAIN-SUFFIX', []))
    domain_keywords = set(rules.get('DOMAIN-KEYWORD', []))
    domain_wildcards = set(rules.get('DOMAIN-WILDCARD', []))
    
    # 移除无效域名
    domains = {d for d in domains if is_valid_domain(d.split(',')[1])}  # 提取域名部分
    domain_suffixes = {d for d in domain_suffixes if is_valid_domain(d.split(',')[1])}
    
    # 处理 DOMAIN 和 DOMAIN-SUFFIX 的关系
    for domain in list(domains):
        domain_name = domain.split(',')[1]
        for suffix in domain_suffixes:
            suffix_name = suffix.split(',')[1]
            if is_subdomain(domain_name, suffix_name):
                domains.remove(domain)
                break
    
    # 处理 DOMAIN-KEYWORD
    for keyword in list(domain_keywords):
        keyword_value = keyword.split(',')[1]
        # 如果关键词出现在任何DOMAIN或DOMAIN-SUFFIX规则中，移除该关键词
        if any(keyword_value in d.split(',')[1] for d in domains) or \
           any(keyword_value in s.split(',')[1] for s in domain_suffixes):
            domain_keywords.remove(keyword)
    
    # 处理 DOMAIN-WILDCARD
    for wildcard in list(domain_wildcards):
        wildcard_value = wildcard.split(',')[1]
        clean_wildcard = wildcard_value.replace('*', '').replace('.', '')
        if any(clean_wildcard in d.split(',')[1].replace('.', '') for d in domains):
            domain_wildcards.remove(wildcard)
    
    # 2. 处理 IP 相关规则
    ip_cidrs = set(rules.get('IP-CIDR', []))
    ip_cidrs6 = set(rules.get('IP-CIDR6', []))
    
    # 确保 IP-CIDR 和 IP-CIDR6 不重复
    for ip in list(ip_cidrs):
        if ':' in ip.split(',')[1]:  # IPv6
            ip_cidrs.remove(ip)
            ip_cidrs6.add(ip)
    
    # 3. 更新优化后的规则集
    if domains:
        optimized['DOMAIN'] = sorted(domains)
    if domain_suffixes:
        optimized['DOMAIN-SUFFIX'] = sorted(domain_suffixes)
    if domain_keywords:
        optimized['DOMAIN-KEYWORD'] = sorted(domain_keywords)
    if domain_wildcards:
        optimized['DOMAIN-WILDCARD'] = sorted(domain_wildcards)
    if ip_cidrs:
        optimized['IP-CIDR'] = sorted(ip_cidrs)
    if ip_cidrs6:
        optimized['IP-CIDR6'] = sorted(ip_cidrs6)
    
    # 4. 复制其他类型的规则
    for rule_type in rules:
        if rule_type not in optimized:
            optimized[rule_type] = sorted(set(rules[rule_type]))
    
    return optimized

def generate_rule_file(merged_data: dict, output_path: str):
    # 在写入之前优化规则
    merged_data['rules'] = optimize_rules(merged_data['rules'])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入元数据
        meta = merged_data['metadata']
        f.write(f"# NAME: {meta['name']}\n")
        f.write(f"# AUTHOR: {meta['author']}\n")
        f.write(f"# REPO: {meta['repo']}\n")
        f.write(f"# UPDATED: {meta['updated']}\n")
        f.write(f"# DESCRIPTION: {meta['description']}\n")
        
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

def generate_module_file(merged_data: dict, module_merger: ModuleMerger, output_path: str):
    """生成模块文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        module_content = module_merger.format_module_content(merged_data)
        f.write(module_content)

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
            generate_rule_file(merged_data, output_path)
            logging.info(f"成功生成规则文件: {rule_set_name}.list")
    
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
                generate_module_file(merged_data, module_merger, output_path)
                logging.info(f"成功生成模块文件: {module_name}.sgmodule")

    # Example configuration
    example_config = {
        "modules": ["modules/advertising_mitm.sgmodule", "modules/AppRemoveAds.sgmodule"],
        "output": "merged_output.sgmodule"
    }
    print("Example configuration:", example_config)

if __name__ == "__main__":
    main() 