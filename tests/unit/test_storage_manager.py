"""存储管理器单元测试"""
import pytest
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import shutil

from src.managers.storage import StorageManager

@pytest.fixture
def storage_manager(config: Dict[str, Any]) -> StorageManager:
    """存储管理器实例"""
    return StorageManager(config["storage"])

@pytest.fixture
def test_storage_dir(test_data_dir: Path) -> Path:
    """测试存储目录"""
    storage_dir = test_data_dir / "storage"
    storage_dir.mkdir(exist_ok=True)
    yield storage_dir
    if storage_dir.exists():
        shutil.rmtree(storage_dir)

@pytest.mark.asyncio
async def test_storage_manager_initialization(storage_manager: StorageManager):
    """测试存储管理器初始化"""
    assert storage_manager is not None
    assert storage_manager.base_dir is not None
    assert storage_manager.max_hot_storage_age > 0

@pytest.mark.asyncio
async def test_get_file_path(storage_manager: StorageManager):
    """测试获取文件路径"""
    # 测试不同文件类型
    video_path = storage_manager.get_file_path("video", "test_video.mp4")
    audio_path = storage_manager.get_file_path("audio", "test_audio.wav")
    
    assert video_path.parent == storage_manager.hot_storage_dir / "videos"
    assert audio_path.parent == storage_manager.hot_storage_dir / "audio"

@pytest.mark.asyncio
async def test_check_storage_space(storage_manager: StorageManager):
    """测试检查存储空间"""
    # 测试存储空间检查
    has_space = await storage_manager.check_storage_space()
    assert isinstance(has_space, bool)

@pytest.mark.asyncio
async def test_cleanup_old_files(storage_manager: StorageManager):
    """测试清理旧文件"""
    # 创建临时测试文件
    temp_file = storage_manager.temp_dir / "temp_test_file.txt"
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file.touch()
    
    # 运行清理
    cleaned_count = await storage_manager.cleanup_old_files()
    
    # 验证结果类型
    assert isinstance(cleaned_count, int)

@pytest.mark.asyncio
async def test_move_to_cold_storage(storage_manager: StorageManager):
    """测试移动到冷存储"""
    # 创建测试文件
    source_file = storage_manager.hot_storage_dir / "videos" / "test_move.mp4"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.touch()
    
    # 移动到冷存储
    result = await storage_manager.move_to_cold_storage(source_file)
    
    # 验证结果
    assert isinstance(result, bool)

@pytest.mark.asyncio
async def test_storage_optimization(storage_manager: StorageManager):
    """测试存储优化"""
    # 运行存储优化
    result = await storage_manager.optimize_storage()
    
    # 验证结果
    assert isinstance(result, dict)
    assert "success" in result

@pytest.mark.asyncio
async def test_storage_monitoring(storage_manager: StorageManager):
    """测试存储监控"""
    # 获取存储统计
    stats = await storage_manager.get_storage_stats()
    
    # 验证统计信息
    assert isinstance(stats, dict) 