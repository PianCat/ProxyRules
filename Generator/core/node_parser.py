"""
节点解析器
负责识别节点的国家/地区，并统计各地区节点数量
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class CountryInfo:
    """国家/地区信息"""
    name: str
    count: int
    pattern: str
    icon_url: str


class NodeParser:
    """节点解析和分类器"""
    
    # 国家/地区元数据（参考 powerfullz_override/convert.js）
    COUNTRIES_META = {
        '香港': {
            'pattern': r'(?i)香港|港|HK|hk|Hong Kong|HongKong|hongkong|🇭🇰',
            'icon': 'https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Hong_Kong.png'
        },
        '台湾': {
            'pattern': r'(?i)台|新北|彰化|TW|Taiwan|🇹🇼',
            'icon': 'https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Taiwan.png'
        },
        '美国': {
            'pattern': r'(?i)美国|美|US|United States|🇺🇸',
            'icon': 'https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/United_States.png'
        },
        '日本': {
            'pattern': r'(?i)日本|川日|东京|大阪|泉日|埼玉|沪日|深日|JP|Japan|🇯🇵',
            'icon': 'https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Japan.png'
        },
        '新加坡': {
            'pattern': r'(?i)新加坡|坡|狮城|SG|Singapore|🇸🇬',
            'icon': 'https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Singapore.png'
        },
    }
    
    # 排除的 ISP 类型节点（落地节点、家宽等）
    ISP_EXCLUDE_PATTERN = r'(?i)家宽|家庭|家庭宽带|商宽|商业宽带|星链|Starlink|落地'
    
    def __init__(self):
        """初始化节点解析器"""
        # 编译正则表达式以提高性能
        self.country_regexes = {
            country: re.compile(meta['pattern'])
            for country, meta in self.COUNTRIES_META.items()
        }
        self.isp_exclude_regex = re.compile(self.ISP_EXCLUDE_PATTERN)
    
    def identify_country(self, node_name: str, exclude_isp: bool = True) -> str:
        """
        识别节点所属国家/地区
        
        Args:
            node_name: 节点名称
            exclude_isp: 是否排除 ISP 类型节点
            
        Returns:
            国家/地区名称，如果不匹配任何已知地区则返回 '其他'
        """
        # 检查是否是 ISP 节点
        if exclude_isp and self.isp_exclude_regex.search(node_name):
            return None  # 返回 None 表示应该排除
        
        # 按顺序检查每个国家/地区
        for country, regex in self.country_regexes.items():
            if regex.search(node_name):
                return country
        
        # 不匹配任何已知地区
        return '其他'
    
    def parse_nodes(self, node_names: List[str], exclude_isp: bool = True) -> Dict[str, int]:
        """
        解析节点列表并统计各地区数量
        
        Args:
            node_names: 节点名称列表
            exclude_isp: 是否排除 ISP 类型节点
            
        Returns:
            地区名称到节点数量的映射
        """
        country_counts = {}
        
        for node_name in node_names:
            country = self.identify_country(node_name, exclude_isp)
            
            # None 表示应该排除的节点
            if country is None:
                continue
            
            # 统计数量
            country_counts[country] = country_counts.get(country, 0) + 1
        
        return country_counts
    
    def get_country_info_list(self, node_names: List[str], 
                             exclude_isp: bool = True,
                             min_count: int = 0) -> List[CountryInfo]:
        """
        获取国家/地区信息列表
        
        Args:
            node_names: 节点名称列表
            exclude_isp: 是否排除 ISP 类型节点
            min_count: 最小节点数量，小于此数量的地区将被过滤
            
        Returns:
            CountryInfo 对象列表，按定义顺序排序（其他地区在最后）
        """
        country_counts = self.parse_nodes(node_names, exclude_isp)
        country_info_list = []
        
        # 按定义顺序添加国家
        for country in self.COUNTRIES_META.keys():
            count = country_counts.get(country, 0)
            if count >= min_count:
                country_info_list.append(CountryInfo(
                    name=country,
                    count=count,
                    pattern=self.COUNTRIES_META[country]['pattern'],
                    icon_url=self.COUNTRIES_META[country]['icon']
                ))
        
        # 添加"其他"地区（如果有）
        other_count = country_counts.get('其他', 0)
        if other_count > 0:  # 其他地区只要有节点就显示
            country_info_list.append(CountryInfo(
                name='其他',
                count=other_count,
                pattern=self._generate_other_pattern(),
                icon_url='https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png'
            ))
        
        return country_info_list
    
    def _generate_other_pattern(self) -> str:
        """
        生成"其他"地区的排除模式
        
        Returns:
            正则表达式字符串，用于匹配"其他"地区节点
        """
        # 构建排除所有已知地区和 ISP 的模式
        exclude_patterns = []
        
        # 排除 ISP
        exclude_patterns.append(r'家宽|家庭|家庭宽带|商宽|商业宽带|星链|Starlink|落地')
        
        # 排除所有已知国家/地区
        for meta in self.COUNTRIES_META.values():
            # 提取模式中的主要关键词（去掉 (?i) 和正则语法）
            pattern = meta['pattern'].replace('(?i)', '')
            exclude_patterns.append(pattern)
        
        # 生成负向前瞻模式
        exclude_pattern = '|'.join(exclude_patterns)
        return f'^(?!.*({exclude_pattern})).*$'
    
    def get_country_group_names(self, node_names: List[str], 
                                exclude_isp: bool = True,
                                min_count: int = 2,
                                suffix: str = '节点') -> List[str]:
        """
        获取国家/地区代理组名称列表
        
        Args:
            node_names: 节点名称列表
            exclude_isp: 是否排除 ISP 类型节点
            min_count: 最小节点数量
            suffix: 组名后缀
            
        Returns:
            代理组名称列表
        """
        country_info_list = self.get_country_info_list(node_names, exclude_isp, min_count)
        return [f"{info.name}{suffix}" for info in country_info_list]
    
    def get_country_filter_pattern(self, country: str, exclude_isp: bool = True) -> str:
        """
        获取国家/地区的过滤模式
        
        Args:
            country: 国家/地区名称
            exclude_isp: 是否在模式中排除 ISP 节点
            
        Returns:
            过滤正则表达式字符串
        """
        if country == '其他':
            return self._generate_other_pattern()
        
        if country not in self.COUNTRIES_META:
            return ''
        
        base_pattern = self.COUNTRIES_META[country]['pattern']
        
        if exclude_isp:
            # 使用正向前瞻和负向前瞻组合
            return f"^(?=.*({base_pattern.replace('(?i)', '')}))(?!.*({self.ISP_EXCLUDE_PATTERN.replace('(?i)', '')})).*$"
        
        return base_pattern
    
    def has_isp_nodes(self, node_names: List[str]) -> bool:
        """
        检查是否包含 ISP 类型节点
        
        Args:
            node_names: 节点名称列表
            
        Returns:
            如果包含 ISP 节点返回 True
        """
        for node_name in node_names:
            if self.isp_exclude_regex.search(node_name):
                return True
        return False


if __name__ == '__main__':
    # 测试代码
    parser = NodeParser()
    
    # 测试节点列表
    test_nodes = [
        '香港 IEPL 01',
        '香港 HGC 02',
        '台湾 HiNet 01',
        '美国 洛杉矶 01',
        '日本 东京 NTT 01',
        '新加坡 01',
        '韩国 首尔 01',
        '香港家宽落地 01',
        '美国星链 01',
        '英国伦敦 01'
    ]
    
    print("=== 测试节点解析器 ===\n")
    
    # 测试识别单个节点
    print("单个节点识别测试:")
    for node in test_nodes:
        country = parser.identify_country(node, exclude_isp=False)
        print(f"  {node} -> {country}")
    
    # 测试统计（排除 ISP）
    print("\n统计测试（排除 ISP）:")
    counts = parser.parse_nodes(test_nodes, exclude_isp=True)
    for country, count in counts.items():
        print(f"  {country}: {count} 个节点")
    
    # 测试获取国家信息列表
    print("\n国家信息列表（最少2个节点）:")
    country_info_list = parser.get_country_info_list(test_nodes, min_count=2)
    for info in country_info_list:
        print(f"  {info.name}: {info.count} 个节点")
    
    # 测试生成代理组名称
    print("\n代理组名称列表:")
    group_names = parser.get_country_group_names(test_nodes)
    for name in group_names:
        print(f"  {name}")
    
    print("\n测试完成！")

