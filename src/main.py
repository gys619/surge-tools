import os
from .rule_merger import RuleMerger
from .module_merger import ModuleMerger
import logging

def generate_rule_file(merged_data: dict, output_path: str):
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
        
        # 写入规则 - 规则已经是排序后的字符串列表
        for rule_type in rules:
            for rule in rules[rule_type]:  # 直接写入规则字符串
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
            merged_data = module_merger.merge_modules(module_name)
            if merged_data:  # 只有在成功获取模块时才生成文件
                output_path = os.path.join(
                    module_merger.config['modules']['output_dir'],
                    f"{module_name}.sgmodule"
                )
                generate_module_file(merged_data, module_merger, output_path)
                logging.info(f"成功生成模块文件: {module_name}.sgmodule")

if __name__ == "__main__":
    main() 