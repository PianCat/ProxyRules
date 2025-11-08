"""
ProxyRules 配置生成器主入口
提供命令行接口，支持生成各种代理工具的配置文件
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from Generator.generators.mihomo_generator import MihomoGenerator
from Generator.generators.stash_generator import StashGenerator
from Generator.generators.loon_generator import LoonGenerator
from Generator.utils.file_helper import FileHelper


class ConfigGenerator:
    """配置文件生成器主类"""
    
    def __init__(self, output_base: Optional[Path] = None):
        """初始化生成器"""
        self.project_root = FileHelper.get_project_root()
        self.output_base = output_base or (self.project_root / "Config")
        
        # 初始化各个生成器
        self.mihomo_gen = MihomoGenerator()
        self.stash_gen = StashGenerator()
        self.loon_gen = LoonGenerator()
    
    def generate_mihomo(self, node_names: Optional[List[str]] = None):
        """
        生成 Mihomo 配置文件
        
        Args:
            node_names: 节点名称列表（用于测试）
        """
        print("\nGenerating Mihomo configuration files...")
        output_dir = self.output_base / "Mihomo"
        
        # Generate YAML configuration files (4 combinations)
        self.mihomo_gen.save_yaml_configs(output_dir, node_names)
        
        # Generate JS override scripts
        self.mihomo_gen.save_js_script(output_dir)
        
        print(f"Mihomo configuration files saved to: {output_dir}")
    
    def generate_stash(self, node_names: Optional[List[str]] = None):
        """
        生成 Stash 配置文件
        
        Args:
            node_names: 节点名称列表（用于测试）
        """
        print("\nGenerating Stash configuration files...")
        output_dir = self.output_base / "Stash"
        
        self.stash_gen.save_stash_configs(output_dir, node_names)
        
        print(f"Stash configuration files saved to: {output_dir}")
    
    def generate_loon(self, node_names: Optional[List[str]] = None):
        """
        生成 Loon 配置文件
        
        Args:
            node_names: 节点名称列表（用于测试）
        """
        print("\nGenerating Loon configuration files...")
        output_dir = self.output_base / "Loon"
        
        self.loon_gen.save_loon_configs(output_dir, node_names)
        
        print(f"Loon configuration files saved to: {output_dir}")
    
    def generate_all(self, node_names: Optional[List[str]] = None):
        """
        生成所有工具的配置文件
        
        Args:
            node_names: 节点名称列表（用于测试）
        """
        print("=" * 60)
        print("ProxyRules Configuration Generator")
        print("=" * 60)
        
        self.generate_mihomo(node_names)
        self.generate_stash(node_names)
        self.generate_loon(node_names)
        
        print("\n" + "=" * 60)
        print("All configuration files generated successfully!")
        print(f"Output directory: {self.output_base}")
        print("=" * 60)


def create_test_nodes() -> List[str]:
    """
    创建测试节点列表
    
    Returns:
        测试节点名称列表
    """
    return [
        '香港 IEPL 01', '香港 IEPL 02', '香港 IEPL 03',
        '台湾 HiNet 01', '台湾 HiNet 02', '台湾 HiNet 03',
        '美国 洛杉矶 01', '美国 洛杉矶 02', '美国 洛杉矶 03',
        '日本 东京 01', '日本 东京 02', '日本 东京 03',
        '新加坡 01', '新加坡 02', '新加坡 03',
        '韩国 首尔 01'
    ]


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ProxyRules 配置文件生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 生成所有工具的配置文件
  python config_generator.py --tool all
  
  # 仅生成 Mihomo 配置
  python config_generator.py --tool mihomo
  
  # 生成多个工具的配置
  python config_generator.py --tool mihomo stash
  
  # 使用测试节点生成配置（用于开发测试）
  python config_generator.py --tool all --test
        '''
    )
    
    parser.add_argument(
        '--tool',
        nargs='+',
        choices=['mihomo', 'stash', 'loon', 'all'],
        default=['all'],
        help='指定要生成的工具配置（可指定多个）'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='使用测试节点生成配置（用于开发测试）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='自定义输出目录（默认为项目根目录的 Config 文件夹）'
    )
    
    args = parser.parse_args()
    
    # 创建生成器实例
    generator = ConfigGenerator()
    
    # 如果指定了自定义输出目录
    if args.output:
        generator.output_base = Path(args.output)
    
    # 准备节点列表（如果是测试模式）
    node_names = create_test_nodes() if args.test else None
    
    if args.test:
        print("\n[Test Mode] Using mock nodes to generate configuration\n")
    
    # 生成配置文件
    tools = args.tool
    
    if 'all' in tools:
        generator.generate_all(node_names)
    else:
        print("=" * 60)
        print("ProxyRules Configuration Generator")
        print("=" * 60)
        
        for tool in tools:
            if tool == 'mihomo':
                generator.generate_mihomo(node_names)
            elif tool == 'stash':
                generator.generate_stash(node_names)
            elif tool == 'loon':
                generator.generate_loon(node_names)
        
        print("\n" + "=" * 60)
        print("Configuration files generated successfully!")
        print(f"Output directory: {generator.output_base}")
        print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

