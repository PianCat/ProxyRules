"""
Stash 配置生成器
生成 Stash 的 .yaml 覆写文件
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from Generator.core.rule_loader import RuleLoader
from Generator.core.proxy_groups import ProxyGroupsGenerator
from Generator.core.node_parser import NodeParser
from Generator.utils.yaml_helper import YamlHelper
from Generator.utils.file_helper import FileHelper
from Generator.utils.base_loader import BaseLoader


class StashGenerator:
    """Stash 配置文件生成器 (YAML 格式)"""
    
    def __init__(self):
        """初始化生成器"""
        self.project_root = FileHelper.get_project_root()
        self.base_loader = BaseLoader()
        self.rule_loader = self.base_loader.rule_loader
        self.proxy_groups_generator = ProxyGroupsGenerator()
        self.node_parser = NodeParser()
    
    def _build_metadata(self) -> Dict[str, str]:
        """
        Build Stash Override metadata
        
        Returns:
            Metadata dictionary
        """
        return {
            'name': 'PianCat Stash Override',
            'desc': "PianCat's Config Override",
            'author': 'PianCat',
            'icon': 'https://fastly.jsdelivr.net/gh/shindgewongxj/WHATSINStash@master/icon/substore.png',
            'category': 'Override'
        }
    
    def _build_dns_config(self, ipv6_enabled: bool = True) -> Dict[str, Any]:
        """
        构建 DNS 配置（Stash 格式，不包含 enable 字段）
        
        Args:
            ipv6_enabled: 是否启用 IPv6（默认 True）
            
        Returns:
            DNS 配置字典
        """
        dns_config = self.base_loader.get_dns_config(ipv6_enabled, fake_ip_mode=True)
        # Stash 不需要 enable 字段
        if 'enable' in dns_config:
            del dns_config['enable']
        return dns_config
    
    def _build_sniffer_config(self) -> Dict[str, Any]:
        """
        构建 Sniffer 配置
        
        Returns:
            Sniffer 配置字典
        """
        return self.base_loader.get_sniffer_config()
    
    def _build_rules(self) -> List[str]:
        """
        构建规则列表
        
        Returns:
            规则字符串列表
        """
        return self.base_loader.get_rules()
    
    def generate_stash_override_config(self, node_names: Optional[List[str]] = None,
                                       ipv6_enabled: bool = True) -> str:
        """
        Generate Stash Override YAML configuration
        
        Args:
            node_names: Node name list
            ipv6_enabled: Whether to enable IPv6 (default True)
            
        Returns:
            Stash Override YAML configuration string
        """
        config = {}
        
        # Add metadata
        config.update(self._build_metadata())
        
        # Add DNS configuration (with #!replace marker)
        config['dns'] = self._build_dns_config(ipv6_enabled)
        
        # Generate proxy groups (always generate, even without node list)
        if node_names:
            proxy_result = self.proxy_groups_generator.generate_all_groups(node_names)
            proxy_groups = proxy_result['proxy-groups']
        else:
            # Even without node list, generate complete proxy-groups structure
            # Use default country node names to ensure complete config structure
            default_country_names = ['香港', '台湾', '新加坡', '日本', '美国']
            default_country_group_names = [f"{name}节点" for name in default_country_names] + ['其他节点']
            
            # Generate base proxy groups
            base_groups = self.proxy_groups_generator.generate_base_groups(default_country_group_names)
            
            # Generate policy proxy groups
            policy_groups = self.proxy_groups_generator.generate_policy_groups(default_country_group_names)
            
            # Generate country proxy groups (using default countries)
            from Generator.core.node_parser import CountryInfo, NodeParser
            node_parser = NodeParser()
            default_country_info = []
            for country_name in default_country_names:
                if country_name in node_parser.COUNTRIES_META:
                    meta = node_parser.COUNTRIES_META[country_name]
                    default_country_info.append(
                        CountryInfo(
                            name=country_name,
                            count=0,
                            pattern=meta['pattern'],
                            icon_url=meta['icon']
                        )
                    )
            # Add "其他节点" group
            default_country_info.append(
                CountryInfo(
                    name='其他',
                    count=0,
                    pattern=node_parser._generate_other_pattern(),
                    icon_url='https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png'
                )
            )
            country_groups = self.proxy_groups_generator.generate_country_groups(default_country_info)
            
            # Combine all proxy groups
            proxy_groups = base_groups + policy_groups + country_groups
        
        # Filter out GLOBAL group for Stash (Stash doesn't need GLOBAL group)
        proxy_groups = [group for group in proxy_groups if group.get('name') != 'GLOBAL']
        config['proxy-groups'] = proxy_groups
        
        # Generate rule-providers
        config['rule-providers'] = self.base_loader.get_rule_providers()
        
        # Generate rules
        config['rules'] = self.base_loader.get_rules()
        
        # Convert to YAML string and add #!replace markers
        yaml_str = YamlHelper.to_yaml_string(config)
        
        # Add empty lines before: dns, proxy-groups, rule-providers, rules
        yaml_str = YamlHelper.add_empty_lines_before_sections(
            yaml_str, 
            ['dns:', 'proxy-groups:', 'rule-providers:', 'rules:']
        )
        
        # Add #!replace markers for override sections
        yaml_str = yaml_str.replace('dns:', 'dns: #!replace')
        yaml_str = yaml_str.replace('proxy-groups:', 'proxy-groups: #!replace')
        yaml_str = yaml_str.replace('rule-providers:', 'rule-providers: #!replace')
        yaml_str = yaml_str.replace('rules:', 'rules: #!replace')
        
        return yaml_str
    
    def generate_stash_full_config(self, node_names: Optional[List[str]] = None,
                                   ipv6_enabled: bool = True) -> str:
        """
        Generate Stash Full YAML configuration
        
        Args:
            node_names: Node name list
            ipv6_enabled: Whether to enable IPv6 (default True)
            
        Returns:
            Stash Full YAML configuration string
        """
        config = {}
        
        # Add mode and log-level
        config['mode'] = 'rule'
        config['log-level'] = 'info'
        
        # Add DNS configuration (without #!replace marker)
        config['dns'] = self._build_dns_config(ipv6_enabled)
        
        # Generate proxy groups (always generate, even without node list)
        if node_names:
            proxy_result = self.proxy_groups_generator.generate_all_groups(node_names)
            proxy_groups = proxy_result['proxy-groups']
        else:
            # Even without node list, generate complete proxy-groups structure
            # Use default country node names to ensure complete config structure
            default_country_names = ['香港', '台湾', '新加坡', '日本', '美国']
            default_country_group_names = [f"{name}节点" for name in default_country_names] + ['其他节点']
            
            # Generate base proxy groups
            base_groups = self.proxy_groups_generator.generate_base_groups(default_country_group_names)
            
            # Generate policy proxy groups
            policy_groups = self.proxy_groups_generator.generate_policy_groups(default_country_group_names)
            
            # Generate country proxy groups (using default countries)
            from Generator.core.node_parser import CountryInfo, NodeParser
            node_parser = NodeParser()
            default_country_info = []
            for country_name in default_country_names:
                if country_name in node_parser.COUNTRIES_META:
                    meta = node_parser.COUNTRIES_META[country_name]
                    default_country_info.append(
                        CountryInfo(
                            name=country_name,
                            count=0,
                            pattern=meta['pattern'],
                            icon_url=meta['icon']
                        )
                    )
            # Add "其他节点" group
            default_country_info.append(
                CountryInfo(
                    name='其他',
                    count=0,
                    pattern=node_parser._generate_other_pattern(),
                    icon_url='https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png'
                )
            )
            country_groups = self.proxy_groups_generator.generate_country_groups(default_country_info)
            
            # Combine all proxy groups
            proxy_groups = base_groups + policy_groups + country_groups
        
        # Filter out GLOBAL group for Stash (Stash doesn't need GLOBAL group)
        proxy_groups = [group for group in proxy_groups if group.get('name') != 'GLOBAL']
        config['proxy-groups'] = proxy_groups
        
        # Generate rule-providers
        config['rule-providers'] = self.base_loader.get_rule_providers()
        
        # Generate rules
        config['rules'] = self.base_loader.get_rules()
        
        # Convert to YAML string (no #!replace markers for full config)
        yaml_str = YamlHelper.to_yaml_string(config)
        
        # Add empty lines before: dns, proxy-groups, rule-providers, rules
        yaml_str = YamlHelper.add_empty_lines_before_sections(
            yaml_str, 
            ['dns:', 'proxy-groups:', 'rule-providers:', 'rules:']
        )
        
        # Add empty line after mode and log-level (if present)
        lines = yaml_str.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            # Add empty line after log-level
            if line.strip() == 'log-level: info' and i + 1 < len(lines) and lines[i + 1].strip() != '':
                new_lines.append('')
        
        yaml_str = '\n'.join(new_lines)
        
        # Add proxy-providers and proxies sections (empty, with comments)
        # Find the position after dns section and before proxy-groups
        lines = yaml_str.split('\n')
        new_lines = []
        inserted = False
        
        for i, line in enumerate(lines):
            # Insert proxy-providers and proxies before proxy-groups
            if not inserted and line.strip().startswith('proxy-groups:'):
                new_lines.append('proxy-providers:')
                new_lines.append('# Your Subscription Proxy Providers Here')
                new_lines.append('# Example:')
                new_lines.append('#   url: https://example.com/proxy.yaml')
                new_lines.append('#   interval: 600')
                new_lines.append('')
                new_lines.append('proxies:')
                new_lines.append('')
                inserted = True
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def save_stash_configs(self, output_dir: Path,
                           node_names: Optional[List[str]] = None):
        """
        Save Stash YAML configuration files (4 files: Full and Override, each with/without IPv6)
        
        Args:
            output_dir: Output directory
            node_names: Node name list
        """
        FileHelper.ensure_dir(output_dir)
        
        # Generate 4 configurations:
        # 1. Full config with IPv6
        content_full = self.generate_stash_full_config(node_names, ipv6_enabled=True)
        filepath_full = output_dir / 'Stash_config_full.yaml'
        FileHelper.write_file(content_full, filepath_full)
        print(f"  [OK] Generated: Stash_config_full.yaml")
        
        # 2. Full config without IPv6
        content_full_no_ipv6 = self.generate_stash_full_config(node_names, ipv6_enabled=False)
        filepath_full_no_ipv6 = output_dir / 'Stash_config_full_no_ipv6.yaml'
        FileHelper.write_file(content_full_no_ipv6, filepath_full_no_ipv6)
        print(f"  [OK] Generated: Stash_config_full_no_ipv6.yaml")
        
        # 3. Override config with IPv6 (use .stoverride extension)
        content_override = self.generate_stash_override_config(node_names, ipv6_enabled=True)
        filepath_override = output_dir / 'Stash_override.stoverride'
        FileHelper.write_file(content_override, filepath_override)
        print(f"  [OK] Generated: Stash_override.stoverride")
        
        # 4. Override config without IPv6 (use .stoverride extension)
        content_override_no_ipv6 = self.generate_stash_override_config(node_names, ipv6_enabled=False)
        filepath_override_no_ipv6 = output_dir / 'Stash_override_no_ipv6.stoverride'
        FileHelper.write_file(content_override_no_ipv6, filepath_override_no_ipv6)
        print(f"  [OK] Generated: Stash_override_no_ipv6.stoverride")


if __name__ == '__main__':
    # 测试代码
    generator = StashGenerator()
    
    print("=== 测试 Stash 生成器 ===\n")
    
    # 测试节点列表
    test_nodes = [
        '香港 IEPL 01', '香港 IEPL 02', '香港 IEPL 03',
        '台湾 HiNet 01', '台湾 HiNet 02',
        '美国 洛杉矶 01', '美国 洛杉矶 02',
        '日本 东京 01', '日本 东京 02',
        '新加坡 01', '新加坡 02'
    ]
    
    # 生成配置
    content = generator.generate_stash_config(test_nodes, ipv6_enabled=False)
    
    print(f"生成的 Stash YAML 配置长度: {len(content)} 字符")
    print(f"包含 #!replace 标记数量: {content.count('#!replace')}")
    
    print("\n测试完成！")

