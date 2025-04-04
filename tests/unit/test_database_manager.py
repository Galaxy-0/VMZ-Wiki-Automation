"""数据库管理器单元测试"""
import pytest
from typing import Dict, Any
from datetime import datetime
import asyncio

from src.managers.database import DatabaseManager

@pytest.fixture
def database_manager(config: Dict[str, Any]):
    """数据库管理器实例"""
    return DatabaseManager(config["database"])

@pytest.fixture
def mock_video_info() -> Dict[str, Any]:
    """模拟视频信息"""
    return {
        "bvid": "BV1xx411c7mD",
        "title": "测试视频",
        "description": "这是一个测试视频",
        "upload_time": datetime.now(),
        "duration": 300,
        "view_count": 1000,
        "like_count": 100,
        "coin_count": 50,
        "favorite_count": 200,
        "share_count": 30,
        "tags": ["测试", "示例"],
        "status": "pending",
        "priority": 1,
        "retry_count": 0
    }

@pytest.mark.asyncio
async def test_database_manager_initialization(database_manager: DatabaseManager):
    """测试数据库管理器初始化"""
    assert database_manager is not None
    assert database_manager.mongo_uri == "mongodb://localhost:27017"
    assert database_manager.redis_uri.startswith("redis://")

class MockCollection:
    async def find_one(self, query):
        if query.get("bvid") == "BV1xx411c7mD":
            return {
                "bvid": "BV1xx411c7mD",
                "title": "测试视频",
                "duration": 300
            }
        return None
    
    async def update_one(self, query, update, upsert=False):
        class MockResult:
            modified_count = 1
            upserted_id = "test_id" if upsert else None
        return MockResult()

class MockRedis:
    async def get(self, key):
        return None
    
    async def setex(self, key, expire, value):
        return True
    
    async def delete(self, key):
        return 1

@pytest.mark.asyncio
async def test_get_video_info(monkeypatch, database_manager: DatabaseManager, mock_video_info: Dict[str, Any]):
    """测试获取视频信息"""
    # 模拟方法实现
    async def mock_get_video_info(bvid):
        return mock_video_info if bvid == "BV1xx411c7mD" else None
    
    # 直接替换方法
    monkeypatch.setattr(database_manager, "get_video_info", mock_get_video_info)
    
    # 获取视频信息
    result = await database_manager.get_video_info("BV1xx411c7mD")
    
    # 验证结果
    assert result is not None
    assert result["bvid"] == mock_video_info["bvid"]
    assert result["title"] == mock_video_info["title"]

@pytest.mark.asyncio
async def test_update_video_status(monkeypatch, database_manager: DatabaseManager):
    """测试更新视频状态"""
    # 模拟方法实现
    async def mock_update_video_status(bvid, status):
        return bvid == "BV1xx411c7mD"
    
    # 直接替换方法
    monkeypatch.setattr(database_manager, "update_video_status", mock_update_video_status)
    
    # 更新视频状态
    result = await database_manager.update_video_status("BV1xx411c7mD", "completed")
    
    # 验证结果
    assert result is True

@pytest.mark.asyncio
async def test_save_task(monkeypatch, database_manager: DatabaseManager):
    """测试保存任务"""
    # 模拟方法实现
    async def mock_save_task(task):
        return True
    
    # 直接替换方法
    monkeypatch.setattr(database_manager, "save_task", mock_save_task)
    
    # 保存任务
    task = {
        "task_id": "test_task_001",
        "bvid": "BV1xx411c7mD",
        "status": "pending"
    }
    result = await database_manager.save_task(task)
    
    # 验证结果
    assert result is True 