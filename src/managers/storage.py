"""存储管理器模块"""
import os
import shutil
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import psutil

class StorageManager:
    """存储管理器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化存储管理器
        
        Args:
            config: 配置信息，包含存储路径等
        """
        self.config = config
        self.base_dir = Path(config.get("base_dir", "storage"))
        self.hot_storage_dir = self.base_dir / "hot"
        self.cold_storage_dir = self.base_dir / "cold"
        self.temp_dir = self.base_dir / "temp"
        self.min_free_space = config.get("min_free_space", 10 * 1024 * 1024 * 1024)  # 10GB
        self.max_hot_storage_age = config.get("max_hot_storage_age", 30)  # 30天
        self.logger = logging.getLogger(__name__)
        
        # 创建必要的目录
        self._create_directories()
    
    def _create_directories(self):
        """创建必要的目录"""
        try:
            self.hot_storage_dir.mkdir(parents=True, exist_ok=True)
            self.cold_storage_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建存储目录失败: {e}")
            raise
    
    def get_file_path(self, file_type: str, filename: str) -> Path:
        """获取文件路径
        
        Args:
            file_type: 文件类型（video/audio/transcript/markdown）
            filename: 文件名
            
        Returns:
            Path: 文件路径
        """
        try:
            if file_type == "video":
                return self.hot_storage_dir / "videos" / filename
            elif file_type == "audio":
                return self.hot_storage_dir / "audio" / filename
            elif file_type == "transcript":
                return self.hot_storage_dir / "transcripts" / filename
            elif file_type == "markdown":
                return self.hot_storage_dir / "markdown" / filename
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
        except Exception as e:
            self.logger.error(f"获取文件路径失败: {e}")
            raise
    
    async def check_storage_space(self) -> bool:
        """检查存储空间
        
        Returns:
            bool: 是否有足够的存储空间
        """
        try:
            disk = psutil.disk_usage(str(self.base_dir))
            return disk.free >= self.min_free_space
        except Exception as e:
            self.logger.error(f"检查存储空间失败: {e}")
            return False
    
    async def cleanup_old_files(self) -> int:
        """清理旧文件
        
        Returns:
            int: 清理的文件数量
        """
        try:
            cleaned_count = 0
            current_time = datetime.now()
            
            # 清理临时文件
            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age > timedelta(days=1):
                        file_path.unlink()
                        cleaned_count += 1
            
            # 清理热存储中的旧文件
            for file_path in self.hot_storage_dir.rglob("*"):
                if file_path.is_file():
                    file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_age > timedelta(days=self.max_hot_storage_age):
                        # 移动到冷存储
                        relative_path = file_path.relative_to(self.hot_storage_dir)
                        cold_path = self.cold_storage_dir / relative_path
                        cold_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(file_path), str(cold_path))
                        cleaned_count += 1
            
            return cleaned_count
        except Exception as e:
            self.logger.error(f"清理旧文件失败: {e}")
            raise
    
    async def move_to_cold_storage(self, file_path: Path) -> bool:
        """将文件移动到冷存储
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否移动成功
        """
        try:
            if not file_path.exists():
                return False
            
            relative_path = file_path.relative_to(self.hot_storage_dir)
            cold_path = self.cold_storage_dir / relative_path
            cold_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(file_path), str(cold_path))
            return True
        except Exception as e:
            self.logger.error(f"移动文件到冷存储失败: {e}")
            return False
    
    async def restore_from_cold_storage(self, file_path: Path) -> bool:
        """从冷存储恢复文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否恢复成功
        """
        try:
            relative_path = file_path.relative_to(self.hot_storage_dir)
            cold_path = self.cold_storage_dir / relative_path
            
            if not cold_path.exists():
                return False
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(cold_path), str(file_path))
            return True
        except Exception as e:
            self.logger.error(f"从冷存储恢复文件失败: {e}")
            return False
    
    async def optimize_storage(self) -> Dict[str, Any]:
        """优化存储空间
        
        Returns:
            Dict[str, Any]: 优化结果
        """
        try:
            # 检查存储空间
            has_space = await self.check_storage_space()
            if not has_space:
                # 清理旧文件
                cleaned_count = await self.cleanup_old_files()
                
                # 再次检查存储空间
                has_space = await self.check_storage_space()
                
                return {
                    "success": has_space,
                    "cleaned_files": cleaned_count,
                    "has_space": has_space
                }
            
            return {
                "success": True,
                "cleaned_files": 0,
                "has_space": True
            }
        except Exception as e:
            self.logger.error(f"优化存储空间失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            Dict[str, Any]: 存储统计信息
        """
        try:
            hot_stats = psutil.disk_usage(str(self.hot_storage_dir))
            cold_stats = psutil.disk_usage(str(self.cold_storage_dir))
            temp_stats = psutil.disk_usage(str(self.temp_dir))
            
            return {
                "hot_storage": {
                    "total": hot_stats.total,
                    "used": hot_stats.used,
                    "free": hot_stats.free,
                    "percent": hot_stats.percent
                },
                "cold_storage": {
                    "total": cold_stats.total,
                    "used": cold_stats.used,
                    "free": cold_stats.free,
                    "percent": cold_stats.percent
                },
                "temp_storage": {
                    "total": temp_stats.total,
                    "used": temp_stats.used,
                    "free": temp_stats.free,
                    "percent": temp_stats.percent
                }
            }
        except Exception as e:
            self.logger.error(f"获取存储统计信息失败: {e}")
            raise 