import requests
import yaml
from datetime import datetime
from typing import Dict, List

class ModuleMerger:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def fetch_module(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    
    def merge_modules(self, module_name: str) -> Dict:
        module_config = self.config['modules']['sources'][module_name]
        content = []
        
        for url in module_config['urls']:
            module_content = self.fetch_module(url)
            content.append(module_content)
        
        return {
            'metadata': {
                'name': module_config['name'],
                'desc': module_config['desc'],
                'author': module_config['author'],
                'repo': module_config['repo'],
                'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'content': '\n'.join(content)
        } 