"""端到端测试"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from src.main import VMZWikiAutomation
from src.processors.task import TaskManager

@pytest.mark.asyncio
async def test_full_workflow(
    config: Dict[str, Any],
    mock_video_info: Dict[str, Any],
    mock_audio_file: str,
    mock_transcript: str,
    mock_markdown_content: str
):
    """测试完整的工作流程"""
    # 初始化系统
    system = VMZWikiAutomation(config)
    task_manager = TaskManager(config)
    
    # 1. 启动系统
    await system.start()
    
    # 2. 添加视频任务
    task_id = task_manager.add_task(mock_video_info)
    assert task_id is not None
    
    # 3. 等待任务完成
    max_wait = 300  # 5分钟超时
    start_time = datetime.now()
    
    while True:
        task_status = task_manager.get_task_status(task_id)
        if task_status == "completed":
            break
        elif task_status == "failed":
            raise Exception("任务处理失败")
        
        if (datetime.now() - start_time).seconds > max_wait:
            raise TimeoutError("任务处理超时")
        
        await asyncio.sleep(1)
    
    # 4. 验证结果
    # 4.1 验证视频信息
    video_info = await system.get_video_info("BV1xx411c7mD")
    assert video_info["bvid"] == "BV1xx411c7mD"
    assert video_info["title"] == "测试视频"
    
    # 4.2 验证Markdown文件
    markdown_path = Path(config["markdown"]["output_dir"]) / f"{video_info['bvid']}.md"
    assert markdown_path.exists()
    
    # 4.3 验证存储状态
    storage_stats = await system.get_storage_stats()
    assert storage_stats["hot_storage"]["file_count"] > 0
    
    # 5. 停止系统
    await system.stop()

@pytest.mark.asyncio
async def test_error_recovery(
    config: Dict[str, Any],
    mock_video_info: Dict[str, Any]
):
    """测试错误恢复机制"""
    # 初始化系统
    system = VMZWikiAutomation(config)
    
    # 1. 启动系统
    await system.start()
    
    # 2. 添加无效视频任务
    task_id = await system.add_video_task("invalid_bvid")
    assert task_id is not None
    
    # 3. 等待任务失败
    max_wait = 60  # 1分钟超时
    start_time = datetime.now()
    
    while True:
        task_status = await system.get_task_status(task_id)
        if task_status == "failed":
            break
        
        if (datetime.now() - start_time).seconds > max_wait:
            raise TimeoutError("任务失败超时")
        
        await asyncio.sleep(1)
    
    # 4. 验证错误日志
    logs = await system.get_task_logs(task_id)
    assert len(logs) > 0
    assert any("下载失败" in log["message"] for log in logs)
    
    # 5. 验证系统状态
    system_status = await system.get_system_status()
    assert system_status["status"] == "running"
    assert system_status["active_tasks"] == 0
    
    # 6. 停止系统
    await system.stop()

@pytest.mark.asyncio
async def test_concurrent_tasks(
    config: Dict[str, Any],
    mock_video_info: Dict[str, Any]
):
    """测试并发任务处理"""
    # 初始化系统
    system = VMZWikiAutomation(config)
    
    # 1. 启动系统
    await system.start()
    
    # 2. 添加多个任务
    task_ids = []
    for i in range(3):
        video_info = mock_video_info.copy()
        video_info["bvid"] = f"BV1xx411c7m{i}"
        task_id = await system.add_video_task(video_info["bvid"])
        task_ids.append(task_id)
    
    # 3. 等待所有任务完成
    max_wait = 300  # 5分钟超时
    start_time = datetime.now()
    
    while True:
        tasks_status = await asyncio.gather(*[
            system.get_task_status(task_id)
            for task_id in task_ids
        ])
        
        if all(status == "completed" for status in tasks_status):
            break
        elif any(status == "failed" for status in tasks_status):
            raise Exception("部分任务处理失败")
        
        if (datetime.now() - start_time).seconds > max_wait:
            raise TimeoutError("任务处理超时")
        
        await asyncio.sleep(1)
    
    # 4. 验证系统状态
    system_status = await system.get_system_status()
    assert system_status["status"] == "running"
    assert system_status["active_tasks"] == 0
    assert system_status["completed_tasks"] == 3
    
    # 5. 停止系统
    await system.stop()

@pytest.mark.asyncio
async def test_system_restart(
    config: Dict[str, Any],
    mock_video_info: Dict[str, Any]
):
    """测试系统重启恢复"""
    # 1. 第一次启动系统
    system1 = VMZWikiAutomation(config)
    await system1.start()
    
    # 2. 添加任务
    task_id = await system1.add_video_task("BV1xx411c7mD")
    
    # 3. 停止系统
    await system1.stop()
    
    # 4. 第二次启动系统
    system2 = VMZWikiAutomation(config)
    await system2.start()
    
    # 5. 验证任务状态
    task_status = await system2.get_task_status(task_id)
    assert task_status in ["pending", "processing", "completed"]
    
    # 6. 停止系统
    await system2.stop() 