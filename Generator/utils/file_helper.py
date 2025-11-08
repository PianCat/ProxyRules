"""
文件处理工具类
提供文件读写、目录管理等功能
"""

from pathlib import Path
from typing import Union, List
import shutil


class FileHelper:
    """文件操作辅助类"""
    
    @staticmethod
    def ensure_dir(dir_path: Union[str, Path]) -> Path:
        """
        确保目录存在，不存在则创建
        
        Args:
            dir_path: 目录路径
            
        Returns:
            Path 对象
        """
        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def read_file(file_path: Union[str, Path]) -> str:
        """
        读取文本文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def write_file(content: str, file_path: Union[str, Path], overwrite: bool = True) -> None:
        """
        Write text file (overwrites existing file by default)
        
        Args:
            content: Content to write
            file_path: Target file path
            overwrite: Whether to overwrite existing file (default True)
        """
        file_path = Path(file_path)
        FileHelper.ensure_dir(file_path.parent)
        
        # Remove existing file if overwrite is enabled
        if overwrite and file_path.exists():
            file_path.unlink()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def clean_directory(dir_path: Union[str, Path], 
                       pattern: str = "*",
                       exclude: List[str] = None) -> int:
        """
        清理目录中的文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件匹配模式
            exclude: 要排除的文件列表
            
        Returns:
            删除的文件数量
        """
        dir_path = Path(dir_path)
        if not dir_path.exists():
            return 0
        
        exclude = exclude or []
        deleted_count = 0
        
        for file in dir_path.glob(pattern):
            if file.is_file() and file.name not in exclude:
                file.unlink()
                deleted_count += 1
        
        return deleted_count
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
        """
        src = Path(src)
        dst = Path(dst)
        
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        FileHelper.ensure_dir(dst.parent)
        shutil.copy2(src, dst)
    
    @staticmethod
    def get_project_root() -> Path:
        """
        获取项目根目录
        
        Returns:
            项目根目录 Path 对象
        """
        # 从当前文件向上查找，直到找到包含 Base 目录的目录
        current = Path(__file__).resolve()
        
        # 向上查找最多 5 层
        for _ in range(5):
            current = current.parent
            if (current / "Base").exists():
                return current
        
        raise RuntimeError("无法找到项目根目录（应包含 Base 目录）")

