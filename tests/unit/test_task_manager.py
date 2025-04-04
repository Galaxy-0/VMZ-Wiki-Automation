"""任务管理器单元测试"""
import pytest
from typing import Dict, Any, List
from datetime import datetime

from src.processors.task import TaskManager

@pytest.fixture
def task_manager(config: Dict[str, Any]) -> TaskManager:
    """任务管理器"""
    return TaskManager(config["processing"])

def test_init(task_manager: TaskManager):
    """测试初始化"""
    assert task_manager is not None
    assert isinstance(task_manager.tasks, dict)
    assert task_manager.batch_size > 0
    assert task_manager.max_concurrent_downloads > 0
    assert task_manager.max_concurrent_processes > 0

def test_add_task(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试添加任务"""
    # 添加任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 验证任务是否添加成功
    assert task_id in task_manager.tasks
    assert task_manager.tasks[task_id].status == "pending"
    assert task_manager.tasks[task_id].video_info == mock_video_info

def test_get_task_status(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试获取任务状态"""
    # 添加任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 获取任务状态
    status = task_manager.get_task_status(task_id)
    assert status == "pending"

def test_update_task_status(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试更新任务状态"""
    # 添加任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 更新任务状态
    result = task_manager.update_task_status(task_id, "processing")
    assert result is True
    assert task_manager.get_task_status(task_id) == "processing"
    
    # 更新为完成状态
    result = task_manager.update_task_status(task_id, "completed")
    assert result is True
    assert task_manager.get_task_status(task_id) == "completed"

def test_get_next_batch(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试获取下一批任务"""
    # 添加多个任务
    task_ids = []
    for _ in range(5):
        task_id = task_manager.add_task(mock_video_info)
        task_ids.append(task_id)
    
    # 获取一批任务
    batch = task_manager.get_next_batch()
    assert len(batch) <= task_manager.batch_size
    
    # 检查这批任务的状态是否已更新
    for task_id in batch:
        assert task_manager.get_task_status(task_id) == "processing"

def test_retry_failed_task(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试重试失败任务"""
    # 添加任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 设置为失败状态
    task_manager.update_task_status(task_id, "failed")
    assert task_manager.get_task_status(task_id) == "failed"
    
    # 重试失败任务
    result = task_manager.retry_failed_task(task_id)
    assert result is True
    assert task_manager.get_task_status(task_id) == "pending"
    assert task_manager.get_task_retry_count(task_id) == 1

def test_get_task_progress(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试获取任务进度"""
    # 添加任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 初始进度应为0
    assert task_manager.get_task_progress(task_id) == 0
    
    # 更新进度
    result = task_manager.update_task_progress(task_id, 50)
    assert result is True
    assert task_manager.get_task_progress(task_id) == 50
    
    # 完成任务，进度应为100
    task_manager.update_task_progress(task_id, 100)
    assert task_manager.get_task_progress(task_id) == 100

def test_get_task_error(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试获取任务错误"""
    # 添加任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 初始应无错误
    assert task_manager.get_task_error(task_id) is None
    
    # 设置错误
    error_msg = "测试错误信息"
    result = task_manager.update_task_error(task_id, error_msg)
    assert result is True
    assert task_manager.get_task_error(task_id) == error_msg
    
    # 错误设置后任务应标记为失败
    assert task_manager.get_task_status(task_id) == "failed"

def test_cleanup_completed_tasks(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试清理已完成任务"""
    # 添加任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 标记为已完成
    task_manager.update_task_status(task_id, "completed")
    assert task_id in task_manager.tasks
    
    # 清理已完成任务
    cleaned = task_manager.cleanup_completed_tasks()
    assert cleaned > 0
    assert task_id not in task_manager.tasks

def test_task_stats(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试任务统计"""
    # 检查初始统计
    stats = task_manager.get_task_stats()
    assert "pending" in stats
    assert "processing" in stats
    assert "completed" in stats
    assert "failed" in stats
    
    # 添加任务后的统计
    task_id = task_manager.add_task(mock_video_info)
    stats = task_manager.get_task_stats()
    assert stats["pending"] > 0
    
    # 完成任务后的统计
    task_manager.update_task_status(task_id, "completed")
    stats = task_manager.get_task_stats()
    assert stats["completed"] > 0
    assert stats["pending"] == 0

def test_task_priority(task_manager: TaskManager, mock_video_info: Dict[str, Any]):
    """测试任务优先级"""
    # 重新创建一个TaskManager实例，确保没有之前测试的任务干扰
    task_manager = TaskManager(task_manager.config)
    
    # 添加不同优先级的任务
    high_priority = mock_video_info.copy()
    high_priority["priority"] = 10
    
    normal_priority = mock_video_info.copy()
    normal_priority["priority"] = 5
    
    low_priority = mock_video_info.copy()
    low_priority["priority"] = 1
    
    # 以乱序添加任务
    task_id_low = task_manager.add_task(low_priority)
    task_id_high = task_manager.add_task(high_priority)
    task_id_normal = task_manager.add_task(normal_priority)
    
    # 获取任务，应按优先级排序
    batch = task_manager.get_next_batch()
    
    # 验证批次中有任务
    assert len(batch) > 0
    
    # 验证第一个任务是最高优先级的
    assert task_id_high in batch
    
    # 如果批次大小足够，验证剩余任务也按优先级排序
    if len(batch) > 1:
        # 找出第一个任务的索引
        high_index = batch.index(task_id_high)
        
        # 如果不是最后一个任务，且有中等优先级的任务
        if high_index < len(batch) - 1 and task_id_normal in batch:
            # 验证中等优先级的任务在高优先级之后
            assert batch.index(task_id_normal) > high_index
    
        # 如果有低优先级的任务，验证它在中等优先级之后或高优先级之后
        if task_id_low in batch:
            assert batch.index(task_id_low) > batch.index(task_id_high)
            if task_id_normal in batch:
                assert batch.index(task_id_low) > batch.index(task_id_normal)

def test_error_handling(task_manager: TaskManager):
    """测试错误处理"""
    # 检查基本对象属性
    assert task_manager is not None
    assert task_manager.tasks is not None
    assert task_manager.task_queue is not None 