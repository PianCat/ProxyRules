"""
规则加载器
负责读取和解析 RemoteRules.yaml 和 RemoteRulesLinkBase.yaml
生成各代理工具所需的规则配置
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from Generator.utils.yaml_helper import YamlHelper
from Generator.utils.file_helper import FileHelper


class RuleLoader:
    """规则加载和 URL 生成器"""
    
    def __init__(self):
        """初始化规则加载器"""
        self.project_root = FileHelper.get_project_root()
        self.rules_file = self.project_root / "Base" / "Rules" / "RemoteRules.yaml"
        self.link_base_file = self.project_root / "Base" / "Rules" / "RemoteRulesLinkBase.yaml"
        
        # 加载规则文件
        self.rules_data = YamlHelper.load_yaml(self.rules_file)
        self.link_base_data = YamlHelper.load_yaml(self.link_base_file)
        
        # 提取关键数据
        self.rules = self.rules_data.get('rules', {})
        self.categories = self.link_base_data.get('Categories', {})
        self.tools_mapping = self.link_base_data.get('Categories_Tools_List', {})
        self.filetype_mapping = self.link_base_data.get('Categories_Filetype_List', {})
    
    def get_tool_type_mapping(self, category: str, proxy_tool: str) -> str:
        """
        获取代理工具类型映射
        
        Args:
            category: 规则分类（如 Sukka、blackmatrix）
            proxy_tool: 代理工具名称（如 Mihomo、Loon）
            
        Returns:
            映射后的工具类型字符串
        """
        if category not in self.tools_mapping:
            return proxy_tool
        
        mapping = self.tools_mapping[category]
        
        # 如果有精确匹配，使用映射值
        if proxy_tool in mapping:
            return mapping[proxy_tool]
        
        # 否则使用 fallback 值
        return mapping.get('fallback', proxy_tool)
    
    def get_filetype_mapping(self, category: str, proxy_tool: str) -> str:
        """
        获取文件类型映射
        
        Args:
            category: 规则分类
            proxy_tool: 代理工具名称
            
        Returns:
            映射后的文件类型字符串
        """
        if category not in self.filetype_mapping:
            return ''
        
        mapping = self.filetype_mapping[category]
        
        # 如果有精确匹配，使用映射值
        if proxy_tool in mapping:
            return mapping[proxy_tool]
        
        # 否则使用 fallback 值
        return mapping.get('fallback', '')
    
    def generate_rule_url(self, rule_name: str, rule_config: Dict[str, Any], 
                          proxy_tool: str) -> Optional[str]:
        """
        生成规则的完整 URL
        
        Args:
            rule_name: 规则名称
            rule_config: 规则配置字典
            proxy_tool: 代理工具类型（Mihomo/Loon/Stash）
            
        Returns:
            完整的规则 URL，如果无法生成则返回 None
        """
        category = rule_config.get('category')
        remotefile = rule_config.get('remotefile', '')
        
        if not category or category not in self.categories:
            return None
        
        # 获取 URL 模板
        url_template = self.categories[category].get('url', '')
        if not url_template:
            return None
        
        # 获取映射后的工具类型
        mapped_tool = self.get_tool_type_mapping(category, proxy_tool)
        
        # 处理 remotefile
        clean_remotefile = remotefile
        if clean_remotefile.startswith('./'):
            clean_remotefile = clean_remotefile[2:]
        
        # 检查 URL 模板是否包含 {filetype} 占位符
        if '{filetype}' in url_template:
            # 需要分离扩展名并使用 filetype 映射
            if '.' in clean_remotefile:
                clean_remotefile = clean_remotefile.rsplit('.', 1)[0]
            filetype = self.get_filetype_mapping(category, proxy_tool)
        else:
            # 不需要 filetype，保留完整路径和扩展名
            filetype = ''
        
        # 替换占位符
        url = url_template.replace('{proxytools}', mapped_tool)
        url = url.replace('{remotefile}', clean_remotefile)
        url = url.replace('{filetype}', filetype)
        
        return url
    
    def _flatten_rules(self, rules_dict: Dict[str, Any], parent_key: str = '') -> Dict[str, Dict[str, Any]]:
        """
        将嵌套的规则字典扁平化
        
        Args:
            rules_dict: 规则字典（可能嵌套）
            parent_key: 父键名
            
        Returns:
            扁平化的规则字典
        """
        flattened = {}
        
        for key, value in rules_dict.items():
            if isinstance(value, dict):
                # 检查是否是规则配置（包含 name、category 等）
                if 'name' in value and 'category' in value:
                    # 这是一个规则配置
                    flattened[key] = value
                else:
                    # 这是嵌套结构，递归处理
                    nested = self._flatten_rules(value, key)
                    flattened.update(nested)
        
        return flattened
    
    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有扁平化的规则
        
        Returns:
            规则名称到规则配置的映射字典
        """
        return self._flatten_rules(self.rules)
    
    def generate_mihomo_rule_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        为 Mihomo/Stash 生成 rule-providers 配置
        
        Returns:
            rule-providers 字典（键为规则键，如 SogouPrivacy，而不是 name）
        """
        rule_providers = {}
        all_rules = self.get_all_rules()
        
        for rule_key, rule_config in all_rules.items():
            name = rule_config.get('name')
            behavior = rule_config.get('behavior', 'classical')
            url = self.generate_rule_url(rule_key, rule_config, 'Mihomo')
            
            if not url or not name:
                continue
            
            # 根据 URL 判断格式
            if url.endswith('.mrs'):
                format_type = 'mrs'
            elif url.endswith('.yaml') or url.endswith('.yml'):
                format_type = 'yaml'
            else:
                format_type = 'text'
            
            # 使用规则键作为 rule-provider 的键（与示例文件一致）
            # 例如：SogouPrivacy 规则键对应 SogouPrivacy rule-provider，即使 name 是 SogouInput
            provider_key = rule_key
            
            # 特殊处理：某些规则键需要映射到不同的 provider 键
            # 目前所有规则键都直接使用，保持与示例文件一致
            
            # 根据格式类型确定路径扩展名
            # 示例文件中：yaml 格式使用 .yaml，text 格式使用 .list，mrs 格式使用 .mrs
            if format_type == 'yaml':
                path_ext = 'yaml'
            elif format_type == 'mrs':
                path_ext = 'mrs'
            else:
                path_ext = 'list'
            
            rule_providers[provider_key] = {
                'type': 'http',
                'behavior': behavior,
                'format': format_type,
                'interval': 86400,
                'url': url,
                'path': f'./ruleset/{name}.{path_ext}'
            }
        
        return rule_providers
    
    def generate_loon_remote_rules(self) -> List[str]:
        """
        为 Loon 生成远程规则列表
        
        Returns:
            规则字符串列表
        """
        remote_rules = []
        all_rules = self.get_all_rules()
        
        # 规则键到策略组名称和标签的映射
        rule_policy_mapping = {
            'AI': ('AI', 'AI'),
            'Telegram': ('Telegram', 'Telegram'),
            'YouTube': ('YouTube', 'YouTube'),
            'YouTubeMusic': ('YouTube', 'YouTube Music'),
            'Netflix': ('Netflix', 'Netflix'),
            'TikTok': ('TikTok', 'TikTok'),
            'Spotify': ('Spotify', 'Spotify'),
            'Steam': ('Steam', 'Steam'),
            'Game': ('Game', 'Game'),
            'E-Hentai': ('E-Hentai', 'E-Hentai'),
            'PornSite': ('PornSite', 'PornSite'),
            'Furrybar': ('PornSite', 'Furrybar'),
            'Stream_US': ('US Media', 'US Media'),
            'Stream_TW': ('Taiwan Media', 'Taiwan Media'),
            'Stream_JP': ('Japan Media', 'Japan Media'),
            'Stream_Global': ('Global Media', 'Global Media'),
            'Apple': ('Apple', 'Apple'),
            'Microsoft': ('Microsoft', 'Microsoft'),
            'Google': ('Google', 'Google'),
            'GoogleFCM': ('Google FCM', 'Google FCM'),
            'SogouPrivacy': ('Sogou Privacy', 'Sogou Privacy'),
            'ADBlock': ('ADBlock', 'ADBlock'),
            'LocalNetwork_Non-IP': ('直接连接', 'LocalNetwork Non-IP'),
            'LocalNetwork_IP': ('直接连接', 'LocalNetwork IP'),
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
            if rule_key not in all_rules:
                continue
            
            rule_config = all_rules[rule_key]
            url = self.generate_rule_url(rule_key, rule_config, 'Loon')
            
            if not url:
                continue
            
            # 获取策略组名称和标签
            if rule_key in rule_policy_mapping:
                policy_name, tag_name = rule_policy_mapping[rule_key]
            else:
                # 默认使用规则名称
                policy_name = rule_config.get('name', rule_key)
                tag_name = policy_name
            
            # Loon 格式: URL, policy=策略组名称, tag=规则标签, enabled=true
            remote_rules.append(f"{url}, policy = {policy_name}, tag = {tag_name}, enabled = true")
        
        return remote_rules
    
    def generate_surge_remote_rules(self) -> List[str]:
        """
        为 Surge 生成远程规则列表
        
        Returns:
            规则字符串列表
        """
        remote_rules = []
        all_rules = self.get_all_rules()
        
        # 规则键到策略组名称、标签和选项的映射
        rule_policy_mapping = {
            'AI': ('AI', 'AI', ''),
            'Telegram': ('Telegram', 'Telegram', ''),
            'YouTube': ('YouTube', 'YouTube', ''),
            'YouTubeMusic': ('YouTube', 'YouTube Music', ''),
            'Netflix': ('Netflix', 'Netflix', ''),
            'TikTok': ('TikTok', 'TikTok', ''),
            'Spotify': ('Spotify', 'Spotify', ''),
            'Steam': ('Steam', 'Steam', ''),
            'Game': ('Game', 'Game', ''),
            'E-Hentai': ('E-Hentai', 'E-Hentai', ''),
            'PornSite': ('PornSite', 'PornSite', ''),
            'Furrybar': ('PornSite', 'Furrybar', ''),
            'Stream_US': ('US Media', 'US Media', ''),
            'Stream_TW': ('Taiwan Media', 'Taiwan Media', ''),
            'Stream_JP': ('Japan Media', 'Japan Media', ''),
            'Stream_Global': ('Global Media', 'Global Media', ''),
            'Apple': ('Apple', 'Apple', ''),
            'Microsoft': ('Microsoft', 'Microsoft', ''),
            'Google': ('Google', 'Google', ''),
            'GoogleFCM': ('Google FCM', 'Google FCM', ''),
            'SogouPrivacy': ('Sogou Privacy', 'Sogou Privacy', ''),
            'ADBlock': ('ADBlock', 'ADBlock', 'extended-matching'),
            'LocalNetwork_Non-IP': ('直接连接', 'LocalNetwork Non-IP', ''),
            'LocalNetwork_IP': ('直接连接', 'LocalNetwork IP', ''),
        }
        
        # 按顺序添加规则
        rule_order = [
            'ADBlock',  # 广告拦截放在最前面
            'AI', 'Telegram', 'YouTube', 'YouTubeMusic', 'Netflix', 
            'TikTok', 'Spotify', 'Steam', 'Game', 'E-Hentai', 
            'PornSite', 'Furrybar', 'Stream_US', 'Stream_TW', 
            'Stream_JP', 'Stream_Global', 'Apple', 'Microsoft', 
            'Google', 'GoogleFCM', 'SogouPrivacy',
            'LocalNetwork_Non-IP', 'LocalNetwork_IP'
        ]
        
        for rule_key in rule_order:
            if rule_key not in all_rules:
                continue
            
            rule_config = all_rules[rule_key]
            url = self.generate_rule_url(rule_key, rule_config, 'Surge')
            
            if not url:
                continue
            
            # 获取策略组名称、标签和选项
            if rule_key in rule_policy_mapping:
                policy_name, tag_name, options = rule_policy_mapping[rule_key]
            else:
                # 默认使用规则名称
                policy_name = rule_config.get('name', rule_key)
                tag_name = policy_name
                options = ''
            
            # 添加注释
            if remote_rules:
                remote_rules.append("")
            remote_rules.append(f"# {tag_name}")
            
            # Surge 格式: RULE-SET,URL,策略组名称,选项
            if options:
                remote_rules.append(f"RULE-SET,{url},{policy_name},{options}")
            else:
                remote_rules.append(f"RULE-SET,{url},{policy_name}")
        
        return remote_rules

    
    def get_rule_names(self) -> List[str]:
        """
        获取所有规则名称列表
        
        Returns:
            规则名称列表
        """
        all_rules = self.get_all_rules()
        return [rule_config.get('name') for rule_config in all_rules.values() 
                if rule_config.get('name')]
    
    def get_rules_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        按分类获取规则
        
        Args:
            category: 分类名称
            
        Returns:
            该分类下的所有规则
        """
        all_rules = self.get_all_rules()
        return {
            key: config for key, config in all_rules.items()
            if config.get('category') == category
        }


if __name__ == '__main__':
    # 测试代码
    loader = RuleLoader()
    
    print("=== 测试规则加载器 ===\n")
    
    # 测试获取所有规则
    all_rules = loader.get_all_rules()
    print(f"总共加载了 {len(all_rules)} 个规则")
    
    # 测试生成 Mihomo rule-providers
    print("\n=== Mihomo Rule Providers (前3个) ===")
    mihomo_providers = loader.generate_mihomo_rule_providers()
    for i, (name, config) in enumerate(list(mihomo_providers.items())[:3]):
        print(f"\n{name}:")
        print(f"  URL: {config['url']}")
        print(f"  Behavior: {config['behavior']}")
        print(f"  Format: {config['format']}")
    
    # 测试生成 Loon 规则
    print("\n=== Loon Remote Rules (前3个) ===")
    loon_rules = loader.generate_loon_remote_rules()
    for rule in loon_rules[:3]:
        print(f"  {rule}")
    
    print("\n测试完成！")

