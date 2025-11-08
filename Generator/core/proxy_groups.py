"""
代理组生成器
负责生成各种代理组配置，包括基础代理组、地区节点组和分流策略组
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from Generator.core.node_parser import NodeParser, CountryInfo


class ProxyGroupsGenerator:
    """代理组生成器"""
    
    # 图标 CDN 基础 URL
    ICON_CDN = "https://cdn.jsdelivr.net/gh"
    
    def __init__(self, node_parser: Optional[NodeParser] = None):
        """
        初始化代理组生成器
        
        Args:
            node_parser: 节点解析器实例，如果不提供则创建新实例
        """
        self.node_parser = node_parser or NodeParser()
    
    def _get_icon_url(self, icon_path: str) -> str:
        """
        获取图标 URL
        
        Args:
            icon_path: 图标路径（相对于 CDN）
            
        Returns:
            完整的图标 URL
        """
        return f"{self.ICON_CDN}/{icon_path}"
    
    def generate_country_groups(self, country_info_list: List[CountryInfo],
                                group_type: str = 'url-test') -> List[Dict[str, Any]]:
        """
        生成地区节点组
        
        Args:
            country_info_list: 国家/地区信息列表
            group_type: 组类型（url-test 或 select）
            
        Returns:
            代理组配置列表
        """
        groups = []
        
        for country_info in country_info_list:
            if country_info.name == '其他':
                # 其他节点组使用 select 类型，使用 exclude-filter
                exclude_pattern = self._generate_exclude_filter_pattern()
                groups.append({
                    'name': '其他节点',
                    'icon': 'https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png',
                    'include-all': True,
                    'type': 'select',
                    'exclude-filter': exclude_pattern
                })
            else:
                # 指定国家/地区节点组
                # 使用简单的 filter 格式，不包含 ^ 和 $，也不排除 ISP
                filter_pattern = country_info.pattern
                group = {
                    'name': f'{country_info.name}节点',
                    'icon': country_info.icon_url,
                    'include-all': True,
                    'filter': filter_pattern,
                    'type': group_type
                }
                
                if group_type == 'url-test':
                    group.update({
                        'url': 'https://cp.cloudflare.com/generate_204',
                        'interval': 60,  # 示例文件中是 60
                        'tolerance': 20,
                        'lazy': False
                    })
                
                groups.append(group)
        
        return groups
    
    def _generate_exclude_filter_pattern(self) -> str:
        """
        生成"其他节点"的排除过滤模式
        
        Returns:
            排除过滤正则表达式字符串
        """
        # 排除所有已定义的国家/地区
        patterns = []
        for country, meta in self.node_parser.COUNTRIES_META.items():
            # 提取模式中的关键词（去掉 (?i) 前缀）
            pattern = meta['pattern'].replace('(?i)', '')
            patterns.append(pattern)
        
        # 组合所有模式
        return f"(?i){'|'.join(patterns)}"
    
    def generate_base_groups(self, country_group_names: List[str]) -> List[Dict[str, Any]]:
        """
        生成基础代理组（选择代理、手动选择）
        
        Args:
            country_group_names: 地区节点组名称列表
            
        Returns:
            基础代理组配置列表
        """
        groups = []
        
        # 1. 选择代理
        # 不包含"故障转移"，直接是地区节点
        selector_proxies = country_group_names + ['手动选择', 'DIRECT']
        groups.append({
            'name': '选择代理',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Proxy.png'),
            'type': 'select',
            'proxies': selector_proxies
        })
        
        # 2. 手动选择
        groups.append({
            'name': '手动选择',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Round_Robin_1.png'),
            'include-all': True,
            'type': 'select'
        })
        
        return groups
    
    def generate_policy_groups(self, country_group_names: List[str]) -> List[Dict[str, Any]]:
        """
        生成分流策略组
        
        Args:
            country_group_names: 地区节点组名称列表
            
        Returns:
            策略组配置列表
        """
        groups = []
        
        # 默认代理列表（用于大多数策略组，使用 YAML 锚点）
        # 注意：这里不直接设置 proxies，而是在 YAML 序列化时处理
        default_proxies = ['选择代理'] + country_group_names + ['手动选择', '直接连接']
        
        # 检查是否有特定地区节点
        has_tw = '台湾节点' in country_group_names
        has_us = '美国节点' in country_group_names
        has_jp = '日本节点' in country_group_names
        
        # 1. AI (使用 &a1 锚点定义)
        groups.append({
            'name': 'AI',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/AI.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_anchor': 'a1'  # 标记为锚点定义
        })
        
        # 2. Telegram (使用 *a1 引用)
        groups.append({
            'name': 'Telegram',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Telegram.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'  # 标记为引用
        })
        
        # 3. YouTube (使用 *a1 引用)
        groups.append({
            'name': 'YouTube',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/YouTube.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 4. Netflix (使用 *a1 引用)
        groups.append({
            'name': 'Netflix',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Netflix.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 5. Spotify (使用 *a1 引用)
        groups.append({
            'name': 'Spotify',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Spotify.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 6. TikTok (使用 *a1 引用)
        groups.append({
            'name': 'TikTok',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/TikTok.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 7. Steam (使用 *a1 引用)
        groups.append({
            'name': 'Steam',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Steam.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 8. Game (使用 *a1 引用)
        groups.append({
            'name': 'Game',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Game.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 9. E-Hentai (使用 *a1 引用)
        groups.append({
            'name': 'E-Hentai',
            'icon': self._get_icon_url('PianCat/CustomProxyRuleset@main/Icons/Ehentai.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 10. PornSite (使用 *a1 引用)
        groups.append({
            'name': 'PornSite',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Pornhub.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 11. US Media
        if has_us:
            groups.append({
                'name': 'US Media',
                'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/United_States.png'),
                'type': 'select',
                'proxies': ['美国节点', '选择代理', '手动选择', '直接连接']
            })
        else:
            groups.append({
                'name': 'US Media',
                'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/United_States.png'),
                'type': 'select',
                'proxies': default_proxies,
                '_yaml_reference': 'a1'
            })
        
        # 12. Taiwan Media
        if has_tw:
            groups.append({
                'name': 'Taiwan Media',
                'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Taiwan.png'),
                'type': 'select',
                'proxies': ['台湾节点', '选择代理', '手动选择', '直接连接']
            })
        else:
            groups.append({
                'name': 'Taiwan Media',
                'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Taiwan.png'),
                'type': 'select',
                'proxies': default_proxies,
                '_yaml_reference': 'a1'
            })
        
        # 13. Japan Media
        if has_jp:
            groups.append({
                'name': 'Japan Media',
                'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Japan.png'),
                'type': 'select',
                'proxies': ['日本节点', '选择代理', '手动选择', '直接连接']
            })
        else:
            groups.append({
                'name': 'Japan Media',
                'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Japan.png'),
                'type': 'select',
                'proxies': default_proxies,
                '_yaml_reference': 'a1'
            })
        
        # 14. Global Media (使用 *a1 引用)
        groups.append({
            'name': 'Global Media',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/DomesticMedia.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 15. Apple
        groups.append({
            'name': 'Apple',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Apple.png'),
            'type': 'select',
            'proxies': ['直接连接', '选择代理'] + country_group_names + ['手动选择']
        })
        
        # 16. Microsoft
        groups.append({
            'name': 'Microsoft',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Microsoft.png'),
            'type': 'select',
            'proxies': ['直接连接', '选择代理'] + country_group_names + ['手动选择']
        })
        
        # 17. Google (使用 *a1 引用)
        groups.append({
            'name': 'Google',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Google_Search.png'),
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        # 18. Google FCM
        groups.append({
            'name': 'Google FCM',
            'icon': self._get_icon_url('PianCat/CustomProxyRuleset@main/Icons/Firebase.png'),
            'type': 'select',
            'proxies': ['Google', '直接连接']
        })
        
        # 19. Sogou Privacy
        groups.append({
            'name': 'Sogou Privacy',
            'icon': self._get_icon_url('PianCat/CustomProxyRuleset@main/Icons/Sougou.png'),
            'type': 'select',
            'proxies': ['直接连接', 'REJECT']
        })
        
        # 20. ADBlock
        groups.append({
            'name': 'ADBlock',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/AdBlack.png'),
            'type': 'select',
            'proxies': ['REJECT-DROP', 'REJECT', '直接连接']
        })
        
        # 21. 直接连接
        groups.append({
            'name': '直接连接',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Direct.png'),
            'type': 'select',
            'proxies': ['DIRECT', '选择代理']
        })
        
        # 22. GLOBAL (使用 *a1 引用)
        groups.append({
            'name': 'GLOBAL',
            'icon': self._get_icon_url('Koolson/Qure@master/IconSet/Color/Global.png'),
            'include-all': True,
            'type': 'select',
            'proxies': default_proxies,
            '_yaml_reference': 'a1'
        })
        
        return groups
    
    def generate_all_groups(self, node_names: List[str], 
                           min_country_nodes: int = 2) -> Dict[str, Any]:
        """
        生成所有代理组（包括基础组、地区组和策略组）
        
        Args:
            node_names: 节点名称列表
            min_country_nodes: 地区最小节点数量
            
        Returns:
            包含所有代理组信息的字典
        """
        # 解析节点获取地区信息
        country_info_list = self.node_parser.get_country_info_list(
            node_names, 
            exclude_isp=True, 
            min_count=min_country_nodes
        )
        
        # 获取地区组名称列表
        country_group_names = [f"{info.name}节点" for info in country_info_list]
        
        # 生成各类代理组
        base_groups = self.generate_base_groups(country_group_names)
        policy_groups = self.generate_policy_groups(country_group_names)
        country_groups = self.generate_country_groups(country_info_list)
        
        # 组合所有代理组（顺序：基础组 -> 策略组 -> 地区组）
        all_groups = base_groups + policy_groups + country_groups
        
        return {
            'proxy-groups': all_groups,
            'country_info': country_info_list,
            'country_group_names': country_group_names
        }


if __name__ == '__main__':
    # 测试代码
    generator = ProxyGroupsGenerator()
    
    # 测试节点列表
    test_nodes = [
        '香港 IEPL 01', '香港 IEPL 02', '香港 IEPL 03',
        '台湾 HiNet 01', '台湾 HiNet 02',
        '美国 洛杉矶 01', '美国 洛杉矶 02', '美国 洛杉矶 03',
        '日本 东京 01', '日本 东京 02',
        '新加坡 01', '新加坡 02',
        '韩国 首尔 01',
        '香港家宽落地 01'
    ]
    
    print("=== 测试代理组生成器 ===\n")
    
    # 生成所有代理组
    result = generator.generate_all_groups(test_nodes, min_country_nodes=2)
    
    print(f"地区信息:")
    for info in result['country_info']:
        print(f"  {info.name}: {info.count} 个节点")
    
    print(f"\n地区组名称: {result['country_group_names']}")
    
    print(f"\n生成的代理组数量: {len(result['proxy-groups'])}")
    print("\n前5个代理组:")
    for group in result['proxy-groups'][:5]:
        print(f"  - {group['name']} ({group['type']})")
    
    print("\n测试完成！")
