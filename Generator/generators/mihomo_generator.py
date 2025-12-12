"""
Mihomo 配置生成器
生成 Mihomo/Clash Meta 的 YAML 覆写文件和 JS 动态脚本
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


class MihomoGenerator:
    """Mihomo 配置文件生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.project_root = FileHelper.get_project_root()
        self.base_loader = BaseLoader()
        self.rule_loader = self.base_loader.rule_loader
        self.proxy_groups_generator = ProxyGroupsGenerator()
        self.node_parser = NodeParser()
    
    def _build_dns_config(self, ipv6_enabled: bool = True,
                          fake_ip_mode: bool = True) -> Dict[str, Any]:
        """
        构建 DNS 配置
        
        Args:
            ipv6_enabled: 是否启用 IPv6（默认 True）
            fake_ip_mode: 是否使用 fake-ip 模式（固定 True）
            
        Returns:
            DNS 配置字典
        """
        return self.base_loader.get_dns_config(ipv6_enabled, fake_ip_mode)
    
    def _build_sniffer_config(self) -> Dict[str, Any]:
        """
        构建域名嗅探配置
        
        Returns:
            Sniffer 配置字典
        """
        return self.base_loader.get_sniffer_config()
    
    def _build_geox_urls(self) -> Dict[str, str]:
        """
        构建 GeoX 数据库 URL
        
        Returns:
            GeoX URL 字典
        """
        return self.base_loader.get_geox_urls()
    
    def _build_rules(self, rule_names: List[str]) -> List[str]:
        """
        构建规则列表
        
        Args:
            rule_names: 规则名称列表（未使用，保留以兼容）
            
        Returns:
            规则字符串列表
        """
        return self.base_loader.get_rules()
    
    def generate_yaml_config(self, node_names: Optional[List[str]] = None,
                            ipv6_enabled: bool = True,
                            full_config: bool = False) -> Dict[str, Any]:
        """
        生成 YAML 格式的配置
        
        Args:
            node_names: 节点名称列表（用于生成代理组）
            ipv6_enabled: 是否启用 IPv6（默认 True）
            full_config: 是否生成完整配置
            
        Returns:
            配置字典
        """
        config = {}
        
        # 如果是完整配置，添加基础设置
        if full_config:
            config.update(self.base_loader.get_full_config_template(ipv6_enabled))
        
        # 添加 DNS 配置
        config['dns'] = self._build_dns_config(ipv6_enabled, fake_ip_mode=True)
        
        # 添加 Sniffer 配置
        config['sniffer'] = self._build_sniffer_config()
        
        # 添加 Geo 相关配置（应该在一块）
        config['geodata-mode'] = True
        if full_config:
            # 完整配置需要添加 geo-auto-update 和 geo-update-interval
            config['geo-auto-update'] = True
            config['geo-update-interval'] = 24
        config['geox-url'] = self._build_geox_urls()
        
        # 生成代理组（始终生成，即使没有节点列表）
        if node_names:
            proxy_result = self.proxy_groups_generator.generate_all_groups(node_names)
            config['proxy-groups'] = proxy_result['proxy-groups']
        else:
            # 即使没有节点列表，也生成完整的代理组结构
            # 使用默认的地区节点名称，这样生成的配置文件结构完整
            default_country_names = ['香港', '台湾', '新加坡', '日本', '美国']
            default_country_group_names = [f"{name}节点" for name in default_country_names] + ['其他节点']
            
            # 生成基础代理组
            base_groups = self.proxy_groups_generator.generate_base_groups(default_country_group_names)
            
            # 生成策略代理组
            policy_groups = self.proxy_groups_generator.generate_policy_groups(default_country_group_names)
            
            # 生成地区代理组（使用默认地区）
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
            # 添加"其他节点"组
            default_country_info.append(
                CountryInfo(
                    name='其他',
                    count=0,
                    pattern=node_parser._generate_other_pattern(),
                    icon_url='https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png'
                )
            )
            country_groups = self.proxy_groups_generator.generate_country_groups(default_country_info)
            
            # 组合所有代理组
            config['proxy-groups'] = base_groups + policy_groups + country_groups
        
        # 生成 rule-providers
        config['rule-providers'] = self.base_loader.get_rule_providers()
        
        # 生成规则
        config['rules'] = self.base_loader.get_rules()
        
        return config
    
    def generate_js_script(self) -> str:
        """
        生成 JS 格式的动态覆写脚本
        
        Returns:
            JS 脚本字符串
        """
        # 使用 JS 脚本生成器生成脚本
        from Generator.scripts.generate_js_script import generate_mihomo_js_script
        return generate_mihomo_js_script()
    
    def save_yaml_configs(self, output_dir: Path, 
                         node_names: Optional[List[str]] = None):
        """
        保存所有 YAML 配置文件（4 种组合）
        
        Args:
            output_dir: 输出目录
            node_names: 节点名称列表（如果为 None，则不包含 proxy-groups）
        """
        FileHelper.ensure_dir(output_dir)
        
        # 生成 4 种组合（IPv6 默认启用）
        combinations = [
            {'ipv6': True, 'full': False},   # 默认配置
            {'ipv6': True, 'full': True},    # 完整配置
            {'ipv6': False, 'full': False},  # 禁用 IPv6
            {'ipv6': False, 'full': True}    # 禁用 IPv6 + 完整配置
        ]
        
        for combo in combinations:
            config = self.generate_yaml_config(
                node_names=node_names,
                ipv6_enabled=combo['ipv6'],
                full_config=combo['full']
            )
            
            filename = f"mihomo_config_ipv6-{1 if combo['ipv6'] else 0}_full-{1 if combo['full'] else 0}.yaml"
            filepath = output_dir / filename
            
            # Convert to YAML string and add empty lines before sections
            yaml_str = YamlHelper.to_yaml_string(config)
            # Add empty lines before: dns, sniffer, geodata-mode, proxy-groups, rule-providers, rules
            yaml_str = YamlHelper.add_empty_lines_before_sections(
                yaml_str, 
                ['dns:', 'sniffer:', 'geodata-mode:', 'proxy-groups:', 'rule-providers:', 'rules:']
            )
            FileHelper.write_file(yaml_str, filepath)
            print(f"  [OK] Generated: {filename}")
    
    def save_js_script(self, output_dir: Path):
        """
        保存所有 JS 覆写脚本（5 个文件）
        
        Args:
            output_dir: 输出目录
        """
        FileHelper.ensure_dir(output_dir)
        
        from Generator.scripts.generate_js_script import (
            generate_mihomo_js_script_args,
            generate_mihomo_js_script_fixed
        )
        
        # 生成 args 版本
        js_script_args = generate_mihomo_js_script_args()
        filepath_args = output_dir / "mihomo_convert_args.js"
        FileHelper.write_file(js_script_args, filepath_args)
        print(f"  [OK] Generated: mihomo_convert_args.js")
        
        # Generate 4 fixed parameter versions
        combinations = [
            {'ipv6': True, 'full': False, 'name': 'mihomo_convert_ipv6-1_full-0.js'},
            {'ipv6': True, 'full': True, 'name': 'mihomo_convert_ipv6-1_full-1.js'},
            {'ipv6': False, 'full': False, 'name': 'mihomo_convert_ipv6-0_full-0.js'},
            {'ipv6': False, 'full': True, 'name': 'mihomo_convert_ipv6-0_full-1.js'},
        ]
        
        for combo in combinations:
            js_script = generate_mihomo_js_script_fixed(combo['ipv6'], combo['full'])
            filepath = output_dir / combo['name']
            FileHelper.write_file(js_script, filepath)
            print(f"  [OK] Generated: {combo['name']}")


if __name__ == '__main__':
    # 测试代码
    generator = MihomoGenerator()
    
    print("=== 测试 Mihomo 生成器 ===\n")
    
    # 测试节点列表
    test_nodes = [
        '香港 IEPL 01', '香港 IEPL 02', '香港 IEPL 03',
        '台湾 HiNet 01', '台湾 HiNet 02',
        '美国 洛杉矶 01', '美国 洛杉矶 02',
        '日本 东京 01', '日本 东京 02',
        '新加坡 01', '新加坡 02'
    ]
    
    # 生成配置
    config = generator.generate_yaml_config(test_nodes, ipv6_enabled=False, full_config=False)
    
    print(f"生成的配置包含:")
    print(f"  - DNS 配置: {len(config['dns'])} 个字段")
    print(f"  - Sniffer 配置: 已启用")
    print(f"  - 代理组: {len(config.get('proxy-groups', []))} 个")
    print(f"  - Rule Providers: {len(config['rule-providers'])} 个")
    print(f"  - 规则: {len(config['rules'])} 条")
    
    print("\n测试完成！")

