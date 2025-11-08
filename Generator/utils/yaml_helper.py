"""
YAML 处理工具类
提供 YAML 文件的读取、写入和序列化功能
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Union, List

try:
    from ruamel.yaml import YAML as RuamelYAML
    from ruamel.yaml.scalarstring import LiteralScalarString
    RUAMEL_AVAILABLE = True
except ImportError:
    RUAMEL_AVAILABLE = False


class YamlHelper:
    """YAML 文件处理辅助类"""
    
    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        加载 YAML 文件
        
        Args:
            file_path: YAML 文件路径
            
        Returns:
            解析后的字典对象
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"YAML 文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: Union[str, Path], 
                  add_document_start: bool = False, overwrite: bool = True) -> None:
        """
        Save data as YAML file (overwrites existing file by default)
        
        Args:
            data: Data to save
            file_path: Target file path
            add_document_start: Whether to add YAML document start marker (---)
            overwrite: Whether to overwrite existing file (default True)
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file if overwrite is enabled
        if overwrite and file_path.exists():
            file_path.unlink()
        
        # Use to_yaml_string to handle YAML anchors and references
        yaml_str = YamlHelper.to_yaml_string(data, add_document_start)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(yaml_str)
    
    @staticmethod
    def add_empty_lines_before_sections(yaml_str: str, sections: List[str]) -> str:
        """
        在指定的配置项前添加空行
        
        Args:
            yaml_str: YAML 字符串
            sections: 需要在前面添加空行的配置项列表（如 ['dns:', 'proxy-groups:', 'rules:']）
            
        Returns:
            处理后的 YAML 字符串
        """
        lines = yaml_str.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            # 检查是否是配置项开始行
            line_stripped = line.strip()
            for section in sections:
                # 检查是否是配置项（可能是 'dns:' 或 'dns: #!replace' 等）
                if line_stripped.startswith(section):
                    # 如果前一行不是空行，且不是第一行，则添加空行
                    if i > 0 and new_lines and new_lines[-1].strip() != '':
                        new_lines.append('')
                    break
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    @staticmethod
    def to_yaml_string(data: Dict[str, Any], add_document_start: bool = False) -> str:
        """
        将数据转换为 YAML 字符串，支持 YAML 锚点和引用
        
        Args:
            data: 要转换的数据
            add_document_start: 是否添加 YAML 文档开始标记
            
        Returns:
            YAML 格式字符串
        """
        # 处理 proxy-groups 中的 YAML 锚点和引用
        anchor_name = None
        if 'proxy-groups' in data:
            proxy_groups = data['proxy-groups']
            
            # 找到第一个标记为锚点的组，移除标记
            for i, group in enumerate(proxy_groups):
                if isinstance(group, dict) and '_yaml_anchor' in group:
                    anchor_name = group['_yaml_anchor']
                    # 移除标记，保留其他属性
                    clean_group = {k: v for k, v in group.items() if not k.startswith('_')}
                    proxy_groups[i] = clean_group
                    break
            
            # 处理引用：将标记为引用的组的 proxies 替换为引用字符串
            if anchor_name:
                for i, group in enumerate(proxy_groups):
                    if isinstance(group, dict) and '_yaml_reference' in group:
                        ref_name = group['_yaml_reference']
                        if ref_name == anchor_name:
                            # 创建引用组（移除标记和 proxies）
                            ref_group = {k: v for k, v in group.items() 
                                       if not k.startswith('_') and k != 'proxies'}
                            # 使用字符串引用，ruamel.yaml 会将其序列化为引用
                            ref_group['proxies'] = f'*{anchor_name}'
                            proxy_groups[i] = ref_group
        
        # 使用 ruamel.yaml 来更好地控制格式
        if RUAMEL_AVAILABLE:
            yaml_obj = RuamelYAML()
            yaml_obj.preserve_quotes = True
            yaml_obj.width = 4096  # 避免长行换行
            # 控制缩进：mapping=2（字典键值对缩进），sequence=4（列表项缩进），offset=2（列表项相对于父级的缩进）
            # 这样列表项会使用 2 空格缩进（与示例文件一致）
            yaml_obj.indent(mapping=2, sequence=4, offset=2)
            yaml_obj.default_flow_style = False
            yaml_obj.allow_unicode = True
            yaml_obj.block_seq_indent = 2  # 列表项缩进（相对于父级）
            
            # 创建字符串流
            from io import StringIO
            stream = StringIO()
            yaml_obj.dump(data, stream)
            yaml_str = stream.getvalue()
            
            # 处理 YAML 锚点格式：在 AI 组的 proxies 行添加锚点标记
            if anchor_name and 'proxy-groups' in data:
                import re
                
                # 查找 AI 组的 proxies 行并添加锚点标记
                lines = yaml_str.split('\n')
                new_lines = []
                in_ai_group = False
                anchor_added = False
                
                for line in lines:
                    if 'name: AI' in line:
                        in_ai_group = True
                        new_lines.append(line)
                    elif in_ai_group and 'proxies:' in line and not anchor_added:
                        # 添加锚点标记
                        # ruamel.yaml 生成的格式是 "    proxies:"，需要添加锚点
                        if '&' not in line:
                            line = line.replace('proxies:', f'proxies: &{anchor_name}')
                        else:
                            # 如果已经有锚点，替换为正确的锚点名称
                            line = re.sub(r'proxies: &\w+', f'proxies: &{anchor_name}', line)
                        new_lines.append(line)
                        anchor_added = True
                    elif in_ai_group and anchor_added and line.strip() and not line.strip().startswith('-') and not line.startswith(' ' * 6):
                        # AI 组结束（检查是否是新组的开始）
                        in_ai_group = False
                        anchor_added = False
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                yaml_str = '\n'.join(new_lines)
                
                # 替换所有引用为正确的引用格式（移除引号）
                reference_pattern = r"proxies: '\*\w+'"
                yaml_str = re.sub(reference_pattern, f'proxies: *{anchor_name}', yaml_str)
                reference_pattern = r'proxies: "\*\w+"'
                yaml_str = re.sub(reference_pattern, f'proxies: *{anchor_name}', yaml_str)
                reference_pattern = r'proxies: \*\w+'
                yaml_str = re.sub(reference_pattern, f'proxies: *{anchor_name}', yaml_str)
                
                # 在代理组之间添加空行（除了第一个组）
                lines = yaml_str.split('\n')
                new_lines = []
                prev_was_group_end = False
                first_group = True
                
                for i, line in enumerate(lines):
                    # 移除 proxy-groups: 后面的空行
                    if line.strip() == 'proxy-groups:' and i + 1 < len(lines) and lines[i + 1].strip() == '':
                        new_lines.append(line)
                        # 跳过下一个空行
                        continue
                    
                    # 检查是否是代理组开始（但不是第一个）
                    if line.strip().startswith('- name:') and not first_group and prev_was_group_end:
                        new_lines.append('')  # 添加空行
                    new_lines.append(line)
                    
                    # 标记第一个组已处理
                    if line.strip().startswith('- name:'):
                        first_group = False
                    
                    # 检查是否是代理组结束（下一个非空行是新的代理组开始）
                    if line.strip() and not line.strip().startswith('-') and not line.strip().startswith('#'):
                        prev_was_group_end = True
                    else:
                        prev_was_group_end = False
                
                yaml_str = '\n'.join(new_lines)
        else:
            # 回退到 PyYAML
            yaml_str = yaml.dump(
                data,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            
            # 手动处理 YAML 锚点格式
            if anchor_name and 'proxy-groups' in data:
                import re
                
                # 移除 _yaml_anchor 和 _yaml_reference 标记行
                lines = yaml_str.split('\n')
                new_lines = []
                for line in lines:
                    if '_yaml_anchor:' in line or '_yaml_reference:' in line:
                        continue
                    new_lines.append(line)
                yaml_str = '\n'.join(new_lines)
                
                # 查找 AI 组的 proxies 行并添加锚点标记
                lines = yaml_str.split('\n')
                new_lines = []
                in_ai_group = False
                anchor_added = False
                indent = 0
                
                for line in lines:
                    if 'name: AI' in line:
                        in_ai_group = True
                        new_lines.append(line)
                    elif in_ai_group and 'proxies:' in line and not anchor_added:
                        indent = len(line) - len(line.lstrip())
                        if '&' in line:
                            line = re.sub(r'proxies: &id\d+', f'proxies: &{anchor_name}', line)
                        else:
                            line = ' ' * indent + f'proxies: &{anchor_name}'
                        new_lines.append(line)
                        anchor_added = True
                    elif in_ai_group and anchor_added and line.strip() and not line.strip().startswith('-') and not line.startswith(' ' * (indent + 2)):
                        in_ai_group = False
                        anchor_added = False
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                yaml_str = '\n'.join(new_lines)
                
                reference_pattern = r'proxies: \*id\d+'
                yaml_str = re.sub(reference_pattern, f'proxies: *{anchor_name}', yaml_str)
                yaml_str = yaml_str.replace(f"proxies: '*{anchor_name}'", f"proxies: *{anchor_name}")
                yaml_str = yaml_str.replace(f'proxies: "*{anchor_name}"', f"proxies: *{anchor_name}")
        
        if add_document_start and not yaml_str.startswith('---'):
            yaml_str = '---\n' + yaml_str
            
        return yaml_str

