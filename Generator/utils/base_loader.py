"""
Base 配置加载器
负责读取 Base 文件夹下的所有配置文件
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from Generator.utils.yaml_helper import YamlHelper
from Generator.utils.file_helper import FileHelper


class BaseLoader:
    """Base 配置文件加载器"""
    
    def __init__(self):
        """初始化加载器"""
        self.project_root = FileHelper.get_project_root()
        self.base_dir = self.project_root / "Base"
        
        # 加载所有配置文件
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有 Base 配置文件"""
        # DNS 配置
        dns_file = self.base_dir / "DNS.yaml"
        dns_data = YamlHelper.load_yaml(dns_file)
        self.dns_ip_list = dns_data.get('DNS_IP', [])
        self.dns_doh_list = dns_data.get('DNS_DoH', [])
        
        # 端口配置
        ports_file = self.base_dir / "Ports.yaml"
        ports_data = YamlHelper.load_yaml(ports_file)
        self.mixed_port = ports_data.get('Mihomo', {}).get('Mixed_Port', 56365)
        self.http_port = ports_data.get('General', {}).get('HTTP_Port', 56365)
        self.socks5_port = ports_data.get('General', {}).get('SOCKS5_Port', 56366)
        
        # Fake IP Filter
        fake_ip_file = self.base_dir / "Fake_IP_Filter.yaml"
        fake_ip_data = YamlHelper.load_yaml(fake_ip_file)
        self.fake_ip_filter = fake_ip_data.get('Fake_IP_Filter', [])
        self.surge_always_real_ip = fake_ip_data.get('Surge_Always_Real_IP', [])
        
        # 测试 URL（使用自定义格式解析，因为文件使用 = 而不是 YAML 格式）
        test_url_file = self.base_dir / "Test_URL.yaml"
        test_url_content = FileHelper.read_file(test_url_file)
        self.internet_test_url = 'http://connect.rom.miui.com/generate_204'
        self.proxy_test_url = 'http://www.gstatic.com/generate_204'
        
        # 解析键值对格式
        for line in test_url_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key == 'internet-test-url':
                    self.internet_test_url = value
                elif key == 'proxy-test-url':
                    self.proxy_test_url = value
        
        # Head 配置
        self.head_mihomo = self._load_head_config('Head_Mihomo.yaml')
        self.head_loon = self._load_head_config('Head_Loon.conf', is_yaml=False)
        self.head_stash = self._load_head_config('Head_Stash.yaml')
        
        # 规则配置（通过 RuleLoader 加载）
        from Generator.core.rule_loader import RuleLoader
        self.rule_loader = RuleLoader()
    
    def _load_head_config(self, filename: str, is_yaml: bool = True) -> str:
        """
        加载 Head 配置文件
        
        Args:
            filename: 文件名
            is_yaml: 是否为 YAML 格式
            
        Returns:
            文件内容字符串
        """
        head_file = self.base_dir / "Head" / filename
        if not head_file.exists():
            return ""
        
        return FileHelper.read_file(head_file)
    
    def get_dns_config(self, ipv6_enabled: bool = True, 
                      fake_ip_mode: bool = True) -> Dict[str, Any]:
        """
        获取 DNS 配置
        
        Args:
            ipv6_enabled: 是否启用 IPv6
            fake_ip_mode: 是否使用 fake-ip 模式
            
        Returns:
            DNS 配置字典
        """
        # 根据 IPv6 状态过滤 DNS IP 列表
        dns_ip_list = []
        for dns_ip in self.dns_ip_list:
            if not ipv6_enabled and ':' in str(dns_ip):
                # IPv6 禁用时，跳过 IPv6 地址
                continue
            dns_ip_list.append(str(dns_ip))
        
        dns_config = {
            'enable': True,
            'ipv6': ipv6_enabled,
            'enhanced-mode': 'fake-ip' if fake_ip_mode else 'redir-host',
            'default-nameserver': dns_ip_list,
            'nameserver': self.dns_doh_list
        }
        
        if fake_ip_mode:
            dns_config['fake-ip-filter'] = self.fake_ip_filter
        
        return dns_config
    
    def get_sniffer_config(self) -> Dict[str, Any]:
        """
        获取 Sniffer 配置
        
        Returns:
            Sniffer 配置字典
        """
        return {
            'sniff': {
                'HTTP': {
                    'ports': [80, '8080-8880'],
                    'override-destination': True
                },
                'TLS': {
                    'ports': [443, 8443]
                },
                'QUIC': {
                    'ports': [443, 8443]
                }
            },
            'skip-domain': [
                'Mijia Cloud',
                'dlg.io.mi.com',
                '+.push.apple.com'
            ]
        }
    
    def get_geox_urls(self) -> Dict[str, str]:
        """
        获取 GeoX 数据库 URL
        
        Returns:
            GeoX URL 字典
        """
        return {
            'geoip': 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip-lite.dat',
            'geosite': 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat',
            'mmdb': 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb',
            'asn': 'https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/GeoLite2-ASN.mmdb'
        }
    
    def get_full_config_template(self, ipv6_enabled: bool = True) -> Dict[str, Any]:
        """
        获取完整配置模板
        
        Args:
            ipv6_enabled: 是否启用 IPv6
            
        Returns:
            完整配置字典
        """
        return {
            'mixed-port': self.mixed_port,
            'allow-lan': True,
            'ipv6': ipv6_enabled,
            'mode': 'rule',
            'unified-delay': True,
            'tcp-concurrent': True,
            'find-process-mode': 'strict',
            'global-client-fingerprint': 'chrome',
            'log-level': 'info',
            'geodata-loader': 'standard',
            'external-controller': ':9999',
            'external-ui': 'ui',
            'external-ui-url': 'https://github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip',
            'disable-keep-alive': True,
            'profile': {
                'store-selected': True
            }
        }
    
    def get_rule_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        获取规则提供者配置
        
        Returns:
            rule-providers 字典
        """
        return self.rule_loader.generate_mihomo_rule_providers()
    
    def get_rules(self) -> List[str]:
        """
        获取规则列表
        
        Returns:
            规则字符串列表
        """
        all_rules = self.rule_loader.get_all_rules()
        rules = []
        
        # 规则映射：规则键 -> (rule-provider 键, 策略组名称)
        # rule-provider 键与规则键一致（如 SogouPrivacy），策略组名称用于规则匹配
        rule_mapping = {
            'AI': ('AI', 'AI'),
            'Telegram': ('Telegram', 'Telegram'),
            'YouTube': ('YouTube', 'YouTube'),
            'YouTubeMusic': ('YouTubeMusic', 'YouTube'),
            'Netflix': ('Netflix', 'Netflix'),
            'TikTok': ('TikTok', 'TikTok'),
            'Spotify': ('Spotify', 'Spotify'),
            'Steam': ('Steam', 'Steam'),
            'Game': ('Game', 'Game'),
            'E-Hentai': ('E-Hentai', 'E-Hentai'),
            'PornSite': ('PornSite', 'PornSite'),
            'Furrybar': ('Furrybar', 'PornSite'),
            'Stream_US': ('Stream_US', 'US Media'),
            'Stream_TW': ('Stream_TW', 'Taiwan Media'),
            'Stream_JP': ('Stream_JP', 'Japan Media'),
            'Stream_Global': ('Stream_Global', 'Global Media'),
            'Apple': ('Apple', 'Apple'),
            'Microsoft': ('Microsoft', 'Microsoft'),
            'Google': ('Google', 'Google'),
            'GoogleFCM': ('GoogleFCM', 'Google FCM'),
            'SogouPrivacy': ('SogouPrivacy', 'Sogou Privacy'),
            'ADBlock': ('ADBlock', 'ADBlock'),
            'LocalNetwork_Non-IP': ('LocalNetwork_Non-IP', '直接连接'),
            'LocalNetwork_IP': ('LocalNetwork_IP', '直接连接'),
        }
        
        # 按顺序添加规则
        rule_order = [
            'AI', 'Telegram', 'YouTube', 'YouTubeMusic', 'Netflix', 
            'TikTok', 'Spotify', 'Steam', 'Game', 'E-Hentai', 
            'PornSite', 'Furrybar', 'Stream_US', 'Stream_TW', 
            'Stream_JP', 'Stream_Global', 'Apple', 'Microsoft', 
            'Google', 'GoogleFCM', 'SogouPrivacy', 'ADBlock',
            'LocalNetwork_Non-IP', 'LocalNetwork_IP'
        ]
        
        for rule_key in rule_order:
            if rule_key in rule_mapping:
                rule_name, policy_name = rule_mapping[rule_key]
                # 检查规则是否存在
                if rule_key in all_rules:
                    rules.append(f'RULE-SET,{rule_name},{policy_name}')
        
        # 添加最终规则
        rules.append('GEOIP,CN,直接连接')
        rules.append('MATCH,选择代理')
        
        return rules


if __name__ == '__main__':
    # 测试代码
    loader = BaseLoader()
    
    print("=== 测试 Base 配置加载器 ===\n")
    
    print(f"DNS IP 列表: {loader.dns_ip_list[:3]}...")
    print(f"DNS DoH 列表: {loader.dns_doh_list[:2]}...")
    print(f"Fake IP Filter 数量: {len(loader.fake_ip_filter)}")
    print(f"Mixed Port: {loader.mixed_port}")
    
    print("\n=== DNS 配置 (IPv6 启用) ===")
    dns_config = loader.get_dns_config(ipv6_enabled=True, fake_ip_mode=True)
    print(f"  IPv6: {dns_config['ipv6']}")
    print(f"  Enhanced Mode: {dns_config['enhanced-mode']}")
    print(f"  Default Nameserver 数量: {len(dns_config['default-nameserver'])}")
    print(f"  Fake IP Filter 数量: {len(dns_config.get('fake-ip-filter', []))}")
    
    print("\n=== 规则提供者数量 ===")
    rule_providers = loader.get_rule_providers()
    print(f"  总共: {len(rule_providers)} 个")
    
    print("\n=== 规则列表 ===")
    rules = loader.get_rules()
    print(f"  总共: {len(rules)} 条规则")
    print(f"  前3条: {rules[:3]}")
    
    print("\n测试完成！")

