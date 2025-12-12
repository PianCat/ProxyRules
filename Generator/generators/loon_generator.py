"""
Loon 配置生成器
生成 Loon 的 .lcf 配置文件
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


class LoonGenerator:
    """Loon 配置文件生成器"""
    
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
        ip_mode = "dual" if ipv6_enabled else "ipv4-only"
        ipv6_vif = "auto" if ipv6_enabled else "off"
        
        # 从 Base 文件获取 DNS 配置
        dns_ip_list = []
        for dns_ip in self.base_loader.dns_ip_list:
            if not ipv6_enabled and ':' in str(dns_ip):
                continue
            dns_ip_list.append(str(dns_ip))
        dns_ip_str = ', '.join(dns_ip_list) + ', system'
        
        doh_str = ', '.join(self.base_loader.dns_doh_list)
        
        # 从 Base 文件获取 Fake IP Filter
        fake_ip_filter_str = ', '.join(self.base_loader.fake_ip_filter)
        
        # 从 Base 文件获取端口和测试 URL
        http_port = self.base_loader.http_port
        socks5_port = self.base_loader.socks5_port
        internet_test_url = self.base_loader.internet_test_url
        proxy_test_url = self.base_loader.proxy_test_url
        
        return f"""[General]
ip-mode = {ip_mode}
ipv6-vif = {ipv6_vif}
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, 162.14.0.0/16, 211.99.96.0/19, 162.159.192.0/24, 162.159.193.0/24, 162.159.195.0/24, fc00::/7, fe80::/10, localhost, *.local, *.lan, captive.apple.com, passenger.t3go.cn, *.ccb.com, wxh.wo.cn, *.abcchina.com, *.abcchina.com.cn
bypass-tun = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.168.0.0/16, 192.88.99.0/24, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 255.255.255.255/32, 2a0e:800:ff80:5::/64, ::/128
sni-sniffing = true
dns-server = {dns_ip_str}
doh-server = {doh_str}
allow-udp-proxy = true
allow-wifi-access = true
wifi-access-http-port = {http_port}
wifi-access-socket5-port = {socks5_port}
internet-test-url = {internet_test_url}
proxy-test-url = {proxy_test_url}
test-timeout = 3
real-ip = {fake_ip_filter_str}
geoip-url = https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country.mmdb
ipasn-url = https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/GeoLite2-ASN.mmdb
disconnect-on-policy-change = true
interface-mode = auto

# resource-parser = https://www.nsloon.com/openloon/import?parser=https://github.com/sub-store-org/Sub-Store/releases/latest/download/sub-store-parser.loon.min.js
"""
    
    def _generate_remote_filter_section(self, node_names: Optional[List[str]] = None) -> str:
        """
        生成 [Remote Filter] 配置段
        
        Args:
            node_names: 节点名称列表
            
        Returns:
            配置字符串
        """
        lines = ["[Remote Filter]"]
        lines.append("# 全部节点筛选")
        lines.append('ALL_Filter = NameRegex, FilterKey = ".*"')
        lines.append("")
        
        # 国家/地区筛选器
        country_filters = {
            '香港': 'HK_Filter',
            '台湾': 'TW_Filter',
            '新加坡': 'SG_Filter',
            '日本': 'JP_Filter',
            '美国': 'US_Filter'
        }
        
        country_patterns = {
            '香港': '(?i)(香港|港|HK|Hong Kong|HongKong|hongkong|🇭🇰)',
            '台湾': '(?i)(台|新北|彰化|TW|Taiwan|🇹🇼)',
            '新加坡': '(?i)(新加坡|坡|狮城|SG|Singapore|🇸🇬)',
            '日本': '(?i)(日本|川日|东京|大阪|泉日|埼玉|沪日|深日|JP|Japan|🇯🇵)',
            '美国': '(?i)(美国|美|US|United States|🇺🇸)'
        }
        
        for country, filter_name in country_filters.items():
            pattern = country_patterns[country]
            lines.append(f"# {country}节点筛选")
            lines.append(f'{filter_name} = NameRegex, FilterKey = "{pattern}"')
            lines.append("")
        
        # 其他节点筛选（排除以上所有地区）
        exclude_pattern = '^(?!.*(香港|港|HK|Hong Kong|HongKong|🇭🇰|台|新北|彰化|TW|Taiwan|🇹🇼|美国|美|US|United States|🇺🇸|日本|川日|东京|大阪|泉日|埼玉|沪日|深日|JP|Japan|🇯🇵|新加坡|坡|狮城|SG|Singapore|🇸🇬))'
        lines.append("# 其他节点筛选（排除以上所有地区）")
        lines.append("# 使用负向预查来排除特定关键词：不含香港、台湾、新加坡、日本、美国")
        lines.append(f'Other_Filter = NameRegex, FilterKey = "{exclude_pattern}"')
        
        return '\n'.join(lines)
    
    def _generate_proxy_group(self, group: Dict[str, Any]) -> str:
        """
        生成单个 Proxy Group 配置行（包含 img-url）
        
        Args:
            group: 代理组配置字典
            
        Returns:
            Loon 格式的策略组配置字符串
        """
        name = group['name']
        group_type = group['type']
        icon = group.get('icon', '')
        img_url_part = f', img-url = {icon}' if icon else ''
        
        # 处理不同类型的代理组
        if group_type == 'select':
            if 'include-all' in group and group['include-all']:
                # 手动切换组，包含所有节点
                if 'filter' in group:
                    # 使用 filter 筛选
                    filter_name = self._get_filter_name_for_group(name)
                    return f"{name} = select, {filter_name}{img_url_part}"
                elif 'exclude-filter' in group:
                    # 其他节点组，使用 exclude-filter
                    filter_name = self._get_filter_name_for_group(name)
                    return f"{name} = select, {filter_name}{img_url_part}"
                else:
                    return f"{name} = select, ALL_Filter{img_url_part}"
            else:
                # 普通选择组
                proxies = ', '.join(group.get('proxies', []))
                return f"{name} = select, {proxies}{img_url_part}"
        
        elif group_type in ['url-test', 'fallback']:
            url = group.get('url', 'https://cp.cloudflare.com/generate_204')
            interval = group.get('interval', 60)
            tolerance = group.get('tolerance', 20)
            
            # 如果有 filter 字段，说明是国家节点组
            if 'filter' in group:
                filter_name = self._get_filter_name_for_group(name)
                return f"{name} = {group_type}, {filter_name}, url = {url}, interval = {interval}, tolerance = {tolerance}{img_url_part}"
            else:
                proxies = ', '.join(group.get('proxies', []))
                return f"{name} = {group_type}, {proxies}, url = {url}, interval = {interval}, tolerance = {tolerance}{img_url_part}"
        
        else:
            # 默认为 select
            proxies = ', '.join(group.get('proxies', []))
            return f"{name} = select, {proxies}{img_url_part}"
    
    def _get_filter_name_for_group(self, group_name: str) -> str:
        """根据组名获取对应的 Filter 名称"""
        filter_mapping = {
            '香港节点': 'HK_Filter',
            '台湾节点': 'TW_Filter',
            '新加坡节点': 'SG_Filter',
            '日本节点': 'JP_Filter',
            '美国节点': 'US_Filter',
            '其他节点': 'Other_Filter',
            '手动选择': 'ALL_Filter'
        }
        return filter_mapping.get(group_name, 'ALL_Filter')
    
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
            # 跳过 GLOBAL 组（Loon 配置中不需要）
            if group.get('name') == 'GLOBAL':
                continue
            try:
                group_line = self._generate_proxy_group(group)
                lines.append(group_line)
            except Exception as e:
                print(f"  Warning: Error generating proxy group {group.get('name', 'unknown')}: {e}")
        
        return '\n'.join(lines)
    
    def _generate_remote_rules_section(self) -> str:
        """
        生成 [Remote Rule] 配置段
        
        Returns:
            配置字符串
        """
        lines = ["[Remote Rule]"]
        
        # 获取所有规则的 URL
        remote_rules = self.rule_loader.generate_loon_remote_rules()
        lines.extend(remote_rules)
        
        return '\n'.join(lines)
    
    def _generate_plugin_section(self) -> str:
        """
        生成 [Plugin] 配置段
        
        Returns:
            配置字符串
        """
        lines = ["[Plugin]"]
        
        # 从 Head_Loon.conf 文件中提取 Plugin 配置
        head_loon_content = self.base_loader.head_loon
        if head_loon_content:
            in_plugin_section = False
            for line in head_loon_content.split('\n'):
                line_stripped = line.strip()
                if line_stripped == '[Plugin]':
                    in_plugin_section = True
                    continue
                elif line_stripped.startswith('[') and line_stripped != '[Plugin]':
                    # 遇到新的配置段，停止读取
                    break
                elif in_plugin_section and line_stripped:
                    # 添加 Plugin 配置行
                    lines.append(line_stripped)
        
        # 如果没有找到 Plugin 配置，添加默认配置
        if len(lines) == 1:  # 只有 [Plugin] 标题
            lines.append("https://raw.githubusercontent.com/Peng-YM/Loon-Gallery/master/loon-gallery.plugin, enable = true")
        
        return '\n'.join(lines)
    
    def _generate_rules_section(self) -> str:
        """
        生成 [Rule] 配置段
        
        Returns:
            配置字符串
        """
        lines = ["[Rule]"]
        lines.append("GEOIP, CN, 直接连接")
        lines.append("FINAL, 选择代理")
        
        return '\n'.join(lines)
    
    def generate_loon_config(self, node_names: Optional[List[str]] = None,
                            ipv6_enabled: bool = True) -> str:
        """
        生成完整的 Loon 配置
        
        Args:
            node_names: 节点名称列表
            ipv6_enabled: 是否启用 IPv6
            
        Returns:
            Loon 配置字符串
        """
        sections = []
        
        # 添加文件头注释
        sections.append("# UpdateTime: 2025.11.05 18:00:00 +0000")
        sections.append("# Author: PianCat")
        sections.append("")
        
        # 生成 General 段
        sections.append(self._generate_general_section(ipv6_enabled))
        
        # 生成 Proxy 段（占位符）
        sections.append("[Proxy]")
        sections.append("")
        
        # 生成 Remote Proxy 段（占位符）
        sections.append("[Remote Proxy]")
        sections.append("")
        
        # 生成 Plugin 段
        sections.append(self._generate_plugin_section())
        sections.append("")
        
        # 生成 Remote Filter 段（始终生成，即使没有节点列表）
        sections.append(self._generate_remote_filter_section(node_names))
        sections.append("")
        
        # 生成 Proxy Group 段（始终生成，即使没有节点列表）
        if node_names:
            proxy_result = self.proxy_groups_generator.generate_all_groups(node_names)
            proxy_groups = proxy_result['proxy-groups']
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
            proxy_groups = base_groups + policy_groups + country_groups
        
        sections.append(self._generate_proxy_groups_section(proxy_groups))
        sections.append("")
        
        # 生成 Remote Rule 段
        sections.append(self._generate_remote_rules_section())
        sections.append("")
        
        # 生成 Rule 段
        sections.append(self._generate_rules_section())
        
        return '\n'.join(sections)
    
    def save_loon_configs(self, output_dir: Path,
                         node_names: Optional[List[str]] = None):
        """
        保存 Loon 配置文件
        
        Args:
            output_dir: 输出目录
            node_names: 节点名称列表
        """
        FileHelper.ensure_dir(output_dir)
        
        # 生成两个版本：默认（IPv6启用）和 禁用IPv6
        configs = [
            {'ipv6': True, 'filename': 'Loon_config.lcf'},
            {'ipv6': False, 'filename': 'Loon_config_no_ipv6.lcf'}
        ]
        
        for config in configs:
            content = self.generate_loon_config(node_names, config['ipv6'])
            filepath = output_dir / config['filename']
            
            FileHelper.write_file(content, filepath)
            print(f"  [OK] Generated: {config['filename']}")


if __name__ == '__main__':
    # 测试代码
    generator = LoonGenerator()
    
    print("=== 测试 Loon 生成器 ===\n")
    
    # 测试节点列表
    test_nodes = [
        '香港 IEPL 01', '香港 IEPL 02', '香港 IEPL 03',
        '台湾 HiNet 01', '台湾 HiNet 02',
        '美国 洛杉矶 01', '美国 洛杉矶 02',
        '日本 东京 01', '日本 东京 02',
        '新加坡 01', '新加坡 02'
    ]
    
    # 生成配置
    content = generator.generate_loon_config(test_nodes, ipv6_enabled=False)
    
    print(f"生成的 Loon 配置长度: {len(content)} 字符")
    print(f"包含配置段数量: {content.count('[')}")
    
    print("\n前 500 个字符:")
    print(content[:500])
    
    print("\n测试完成！")

