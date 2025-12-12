"""
Surge 配置生成器
生成 Surge 的 .conf 配置文件
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from Generator.core.rule_loader import RuleLoader
from Generator.core.proxy_groups import ProxyGroupsGenerator
from Generator.core.node_parser import NodeParser
from Generator.utils.file_helper import FileHelper
from Generator.utils.base_loader import BaseLoader


class SurgeGenerator:
    """Surge 配置文件生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.project_root = FileHelper.get_project_root()
        self.base_loader = BaseLoader()
        self.rule_loader = self.base_loader.rule_loader
        self.proxy_groups_generator = ProxyGroupsGenerator()
        self.node_parser = NodeParser()
    
    def _generate_general_section(self, ipv6_enabled: bool = True) -> str:
        """
        生成 [General] 配置段
        
        Args:
            ipv6_enabled: 是否启用 IPv6（默认 True）
            
        Returns:
            配置字符串
        """
        # IPv6 设置
        ipv6_value = "true" if ipv6_enabled else "false"
        ipv6_vif_value = "auto" if ipv6_enabled else "disabled"
        
        # 从 Base 文件获取 DNS 配置
        dns_ip_list = []
        for dns_ip in self.base_loader.dns_ip_list:
            if not ipv6_enabled and ':' in str(dns_ip):
                continue
            dns_ip_list.append(str(dns_ip))
        dns_ip_str = ', '.join(dns_ip_list) + ', system'
        
        # DoH 服务器
        doh_list = self.base_loader.dns_doh_list
        doh_str = ', '.join(doh_list) if doh_list else ''
        
        # 从 Base 文件获取端口和测试 URL
        http_port = self.base_loader.http_port
        socks5_port = self.base_loader.socks5_port
        internet_test_url = self.base_loader.internet_test_url
        proxy_test_url = self.base_loader.proxy_test_url
        
        # 从 Base 文件获取 Surge Always Real IP 列表
        # Surge 使用专门的 Surge_Always_Real_IP 列表
        always_real_ip = ', '.join(self.base_loader.surge_always_real_ip)
        
        general_config = f"""[General]
# 日志级别
loglevel = notify
show-error-page-for-reject = true

# 网络访问
allow-wifi-access = true
wifi-access-http-port = {http_port}
wifi-access-socks5-port = {socks5_port}

# All Hybrid 网络并发
all-hybrid = false

# IPv6 支持
ipv6 = {ipv6_value}
ipv6-vif = {ipv6_vif_value}

# 测试
test-timeout = 3
internet-test-url = {internet_test_url}
proxy-test-url = {proxy_test_url}

# GeoIP 数据库
geoip-maxmind-url = https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/Country.mmdb

# DNS 设置
dns-server = {dns_ip_str}"""
        
        # 添加 DoH 配置（如果有）
        if doh_str:
            general_config += f"\nencrypted-dns-server = {doh_str}"
        
        general_config += f"""
hijack-dns = 8.8.8.8:53, 8.8.4.4:53
read-etc-hosts = true

# 跳过代理
exclude-simple-hostnames = true
skip-proxy = 192.168.0.0/24, 10.0.0.0/8, 172.16.0.0/12, 127.0.0.1, localhost, *.local, captive.apple.com, passenger.t3go.cn, *.ccb.com, wxh.wo.cn, *.abcchina.com, *.abcchina.com.cn

# Always Real IP (Surge 专用列表)
always-real-ip = {always_real_ip}

# 其他设置
use-default-policy-if-wifi-not-primary = false
disable-geoip-db-auto-update = false
udp-policy-not-supported-behaviour = REJECT
http-api-web-dashboard = false
"""
        
        return general_config
    
    def _generate_proxy_section(self) -> str:
        """
        生成 [Proxy] 配置段
        
        Returns:
            配置字符串
        """
        # Surge 的 DIRECT 是内置策略，不需要在 [Proxy] 段定义
        return """[Proxy]
# 在此添加你的代理节点
# 使用 #!include <ProfileName>.conf 关联其他配置，或在下方的 `Proxies` 中添加订阅地址（仅限单条），若使用 include 则需要删除下方的 policy-path 字段
"""
    
    def _get_country_pattern_for_surge(self, group_name: str) -> str:
        """
        根据组名获取对应的国家/地区匹配模式（Surge 格式）
        
        Args:
            group_name: 代理组名称
            
        Returns:
            正则表达式模式
        """
        # 从 node_parser 获取国家元数据
        country_name = group_name.replace('节点', '')
        
        if country_name in self.node_parser.COUNTRIES_META:
            pattern = self.node_parser.COUNTRIES_META[country_name]['pattern']
            # 移除 (?i) 前缀，Surge 默认不区分大小写
            pattern = pattern.replace('(?i)', '')
            return pattern
        
        # 其他节点的排除模式
        if country_name == '其他':
            patterns = []
            for country, meta in self.node_parser.COUNTRIES_META.items():
                pattern = meta['pattern'].replace('(?i)', '')
                patterns.append(pattern)
            return '|'.join(patterns)
        
        return '.*'
    
    def _generate_proxy_group(self, group: Dict[str, Any]) -> str:
        """
        生成单个 Proxy Group 配置行
        
        Args:
            group: 代理组配置字典
            
        Returns:
            Surge 格式的策略组配置字符串
        """
        name = group['name']
        group_type = group['type']
        icon = group.get('icon', '')
        
        # 处理不同类型的代理组
        if group_type == 'select':
            if 'include-all' in group and group['include-all']:
                # 手动选择组，包含所有节点
                if 'exclude-filter' in group:
                    # 其他节点组，使用排除过滤
                    exclude_pattern = self._get_country_pattern_for_surge(name)
                    return f"{name} = select, include-other-group=Proxies, update-interval=0, policy-regex-filter=^(?!.*({exclude_pattern})), icon-url={icon}"
                else:
                    # 手动选择，包含所有节点
                    return f"{name} = select, include-other-group=Proxies, update-interval=0, icon-url={icon}"
            else:
                # 普通选择组
                proxies = ', '.join(group.get('proxies', []))
                return f"{name} = select, {proxies}, icon-url={icon}"
        
        elif group_type == 'url-test':
            # Surge 使用 smart 类型实现类似 url-test 的功能
            url = group.get('url', 'http://www.gstatic.com/generate_204')
            
            # 如果有 filter 字段，说明是国家节点组
            if 'filter' in group:
                filter_pattern = self._get_country_pattern_for_surge(name)
                return f"{name} = smart, include-other-group=Proxies, update-interval=0, policy-regex-filter=({filter_pattern}), icon-url={icon}"
            else:
                proxies = ', '.join(group.get('proxies', []))
                return f"{name} = smart, {proxies}, icon-url={icon}"
        
        else:
            # 默认为 select
            proxies = ', '.join(group.get('proxies', []))
            return f"{name} = select, {proxies}, icon-url={icon}"
    
    def _generate_proxy_groups_section(self, proxy_groups: List[Dict[str, Any]]) -> str:
        """
        生成 [Proxy Group] 配置段
        
        Args:
            proxy_groups: 代理组列表
            
        Returns:
            配置字符串
        """
        lines = ["[Proxy Group]"]
        
        for group in proxy_groups:
            # 跳过 GLOBAL 组（Surge 配置中不需要）
            if group.get('name') == 'GLOBAL':
                continue
            try:
                group_line = self._generate_proxy_group(group)
                lines.append(group_line)
            except Exception as e:
                print(f"  Warning: Error generating proxy group {group.get('name', 'unknown')}: {e}")
        
        # 添加 Proxies 组（用于存放订阅地址）
        lines.append("")
        lines.append("# Proxies")
        lines.append("Proxies = select, policy-path=<Your Node List Link Here>, update-interval=0, no-alert=0, hidden=0, include-all-proxies=1, icon-url=https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Proxy.png")
        
        return '\n'.join(lines)
    
    def _generate_rule_section(self) -> str:
        """
        生成 [Rule] 配置段
        
        Returns:
            配置字符串
        """
        lines = ["[Rule]"]
        
        # 获取所有规则的 URL
        remote_rules = self.rule_loader.generate_surge_remote_rules()
        lines.extend(remote_rules)
        
        # 添加基础规则
        lines.append("")
        lines.append("# 局域网地址")
        lines.append("RULE-SET,LAN,直接连接")
        lines.append("")
        lines.append("# GeoIP CN")
        lines.append("GEOIP,CN,直接连接")
        lines.append("")
        lines.append("# Final")
        lines.append("FINAL,选择代理,dns-failed")
        
        return '\n'.join(lines)
    
    def generate_surge_config(self, node_names: Optional[List[str]] = None,
                             ipv6_enabled: bool = True) -> str:
        """
        生成完整的 Surge 配置
        
        Args:
            node_names: 节点名称列表
            ipv6_enabled: 是否启用 IPv6
            
        Returns:
            Surge 配置字符串
        """
        sections = []
        
        # 添加文件头注释
        sections.append("# Surge Configuration")
        sections.append("# Author: PianCat")
        sections.append("# Update: 2025-11-26")
        sections.append("# Surge Version: 5.x")
        sections.append("")
        
        # 生成 General 段
        sections.append(self._generate_general_section(ipv6_enabled))
        sections.append("")
        
        # 生成 Proxy 段
        sections.append(self._generate_proxy_section())
        sections.append("")
        
        # 生成 Proxy Group 段
        if node_names:
            proxy_result = self.proxy_groups_generator.generate_all_groups(node_names)
            proxy_groups = proxy_result['proxy-groups']
        else:
            # 即使没有节点列表，也生成完整的代理组结构
            default_country_names = ['香港', '台湾', '新加坡', '日本', '美国']
            default_country_group_names = [f"{name}节点" for name in default_country_names] + ['其他节点']
            
            # 生成基础代理组
            base_groups = self.proxy_groups_generator.generate_base_groups(default_country_group_names)
            
            # 生成策略代理组
            policy_groups = self.proxy_groups_generator.generate_policy_groups(default_country_group_names)
            
            # 生成地区代理组（使用默认地区）
            from Generator.core.node_parser import CountryInfo
            default_country_info = []
            for country_name in default_country_names:
                if country_name in self.node_parser.COUNTRIES_META:
                    meta = self.node_parser.COUNTRIES_META[country_name]
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
                    pattern=self.node_parser._generate_other_pattern(),
                    icon_url='https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png'
                )
            )
            country_groups = self.proxy_groups_generator.generate_country_groups(default_country_info)
            
            # 组合所有代理组
            proxy_groups = base_groups + policy_groups + country_groups
        
        sections.append(self._generate_proxy_groups_section(proxy_groups))
        sections.append("")
        
        # 生成 Rule 段
        sections.append(self._generate_rule_section())
        
        return '\n'.join(sections)
    
    def save_surge_configs(self, output_dir: Path,
                          node_names: Optional[List[str]] = None):
        """
        保存 Surge 配置文件
        
        Args:
            output_dir: 输出目录
            node_names: 节点名称列表
        """
        FileHelper.ensure_dir(output_dir)
        
        # 生成两个版本：默认（IPv6启用）和 禁用IPv6
        configs = [
            {'ipv6': True, 'filename': 'Surge_config.conf'},
            {'ipv6': False, 'filename': 'Surge_config_no_ipv6.conf'}
        ]
        
        for config in configs:
            content = self.generate_surge_config(node_names, config['ipv6'])
            filepath = output_dir / config['filename']
            
            FileHelper.write_file(content, filepath)
            print(f"  [OK] Generated: {config['filename']}")


if __name__ == '__main__':
    # 测试代码
    generator = SurgeGenerator()
    
    print("=== 测试 Surge 生成器 ===\n")
    
    # 测试节点列表
    test_nodes = [
        '香港 IEPL 01', '香港 IEPL 02', '香港 IEPL 03',
        '台湾 HiNet 01', '台湾 HiNet 02',
        '美国 洛杉矶 01', '美国 洛杉矶 02',
        '日本 东京 01', '日本 东京 02',
        '新加坡 01', '新加坡 02'
    ]
    
    # 生成配置
    content = generator.generate_surge_config(test_nodes, ipv6_enabled=True)
    
    print(f"生成的 Surge 配置长度: {len(content)} 字符")
    print(f"包含配置段数量: {content.count('[')}个")
    
    print("\n前 800 个字符:")
    print(content[:800])
    
    print("\n测试完成！")
