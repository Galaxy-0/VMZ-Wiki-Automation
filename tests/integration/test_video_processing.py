"""视频处理流程集成测试"""
import pytest
from datetime import datetime
from typing import Dict, Any

from src.collectors.video import VideoCollector
from src.processors.task import TaskManager
from src.processors.audio import AudioProcessor
from src.processors.speech import SpeechRecognizer
from src.generators.markdown import MarkdownGenerator
from src.managers.storage import StorageManager
from src.managers.database import DatabaseManager

@pytest.mark.asyncio
async def test_video_processing_flow(
    config: Dict[str, Any],
    mock_video_info: Dict[str, Any],
    mock_audio_file: str,
    mock_transcript: str,
    mock_markdown_content: str
):
    """测试完整的视频处理流程"""
    # 初始化各个组件
    video_collector = VideoCollector(config["bilibili"])
    task_manager = TaskManager(config)
    audio_processor = AudioProcessor(config["audio"])
    speech_recognizer = SpeechRecognizer(config["speech"])
    markdown_generator = MarkdownGenerator(config["markdown"])
    storage_manager = StorageManager(config["storage"])
    database_manager = DatabaseManager(config["database"])
    
    # 1. 获取视频信息
    video_info = await video_collector.get_video_info("BV1xx411c7mD")
    assert video_info["bvid"] == "BV1xx411c7mD"
    assert video_info["title"] == "测试视频"
    
    # 2. 创建任务
    task_id = task_manager.add_task(video_info)
    task = task_manager.get_task_status(task_id)
    assert task == "pending"
    assert task_id is not None
    
    # 3. 下载视频
    video_path = await video_collector.download_video(video_info["bvid"])
    assert video_path.exists()
    
    # 4. 提取音频
    audio_path = await audio_processor.extract_audio(video_path)
    assert audio_path.exists()
    
    # 5. 语音识别
    transcript = await speech_recognizer.transcribe(audio_path)
    assert transcript == mock_transcript
    
    # 6. 生成Markdown
    markdown_path = await markdown_generator.generate(
        video_info,
        transcript
    )
    assert markdown_path.exists()
    
    # 7. 更新任务状态
    task_manager.update_task_status(task_id, "completed")
    
    # 8. 保存到数据库
    await database_manager.save_video_info(video_info)
    await database_manager.save_task_info(task)
    
    # 9. 清理临时文件
    await storage_manager.cleanup_old_files()
    
    # 验证最终结果
    saved_video = await database_manager.get_video_info(video_info["bvid"])
    assert saved_video["bvid"] == video_info["bvid"]
    
    saved_task = await database_manager.get_task_info(task_id)
    assert saved_task["status"] == "completed"
    
    # 清理测试文件
    video_path.unlink(missing_ok=True)
    audio_path.unlink(missing_ok=True)
    markdown_path.unlink(missing_ok=True)

@pytest.mark.asyncio
async def test_error_handling(
    config: Dict[str, Any],
    mock_video_info: Dict[str, Any]
):
    """测试错误处理流程"""
    # 初始化组件
    video_collector = VideoCollector(config["bilibili"])
    task_manager = TaskManager(config)
    database_manager = DatabaseManager(config["database"])
    
    # 1. 创建任务
    task_id = task_manager.add_task(mock_video_info)
    
    # 2. 模拟下载失败
    with pytest.raises(Exception):
        await video_collector.download_video("invalid_bvid")
    
    # 3. 更新任务状态为失败
    task_manager.update_task_status(task_id, "failed")
    
    # 4. 验证任务状态
    saved_task = await database_manager.get_task_info(task_id)
    assert saved_task["status"] == "failed"
    
    # 5. 验证错误日志
    logs = await database_manager.get_task_logs(task_id)
    assert len(logs) > 0
    assert any("下载失败" in log["message"] for log in logs)

@pytest.mark.asyncio
async def test_concurrent_processing(
    config: Dict[str, Any],
    mock_video_info: Dict[str, Any]
):
    """测试并发处理"""
    # 初始化组件
    task_manager = TaskManager(config)
    database_manager = DatabaseManager(config["database"])
    
    # 创建多个任务
    tasks = []
    for i in range(3):
        video_info = mock_video_info.copy()
        video_info["bvid"] = f"BV1xx411c7m{i}"
        task_id = task_manager.add_task(video_info)
        tasks.append(task_id)
    
    # 并发更新任务状态
    import asyncio
    await asyncio.gather(*[
        task_manager.update_task_status(task_id, "processing")
        for task_id in tasks
    ])
    
    # 验证所有任务状态
    for task_id in tasks:
        saved_task = await database_manager.get_task_info(task_id)
        assert saved_task["status"] == "processing"
    
    # 清理任务
    await asyncio.gather(*[
        task_manager.delete_task(task_id)
        for task_id in tasks
    ]) 