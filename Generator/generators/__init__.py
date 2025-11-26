"""
生成器模块：为各个代理工具生成配置文件
"""

from .mihomo_generator import MihomoGenerator
from .stash_generator import StashGenerator
from .loon_generator import LoonGenerator
from .surge_generator import SurgeGenerator

__all__ = ['MihomoGenerator', 'StashGenerator', 'LoonGenerator', 'SurgeGenerator']
