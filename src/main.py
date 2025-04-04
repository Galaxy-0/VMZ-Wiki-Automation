"""VMZ Wiki自动化主程序"""
import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from datetime import datetime

from src.collectors.video import VideoCollector
from src.processors.audio import AudioProcessor
from src.processors.speech import SpeechRecognizer
from src.generators.markdown import MarkdownGenerator
from src.managers.storage import StorageManager
from src.managers.database import DatabaseManager
from src.filters.video import VideoFilter
from src.processors.task import TaskManager

class VMZWikiAutomation:
    """VMZ Wiki自动化系统主类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化系统
        
        Args:
            config: 系统配置信息
        """
        self.config = config
        self.logger = self._setup_logger()
        
        # 初始化组件
        self.video_collector = VideoCollector(config["bilibili"])
        self.audio_processor = AudioProcessor(config["audio"])
        self.speech_recognizer = SpeechRecognizer(config["speech"])
        self.markdown_generator = MarkdownGenerator(config["markdown"])
        self.storage_manager = StorageManager(config["storage"])
        self.database_manager = DatabaseManager(config["database"])
        self.video_filter = VideoFilter(config["video_filter"])
        self.task_manager = TaskManager(config)
        
        # 系统状态
        self.is_running = False
        self.processing_tasks = set()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器
        
        Returns:
            logging.Logger: 日志记录器
        """
        logger = logging.getLogger("vmz_wiki")
        logger.setLevel(logging.INFO)
        
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器
        log_file = log_dir / f"vmz_wiki_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    async def start(self):
        """启动系统"""
        try:
            # 连接数据库
            await self.database_manager.connect()
            
            # 检查存储空间
            has_space = await self.storage_manager.check_storage_space()
            if not has_space:
                self.logger.warning("存储空间不足，开始清理旧文件")
                await self.storage_manager.cleanup_old_files()
            
            self.logger.info("系统启动完成")
        except Exception as e:
            self.logger.error(f"系统启动失败: {e}")
            raise
    
    async def stop(self):
        """停止系统"""
        try:
            # 断开数据库连接
            await self.database_manager.disconnect()
            
            # 清理语音识别器资源
            self.speech_recognizer.cleanup()
            
            self.logger.info("系统停止完成")
        except Exception as e:
            self.logger.error(f"系统停止失败: {e}")
    
    async def add_video_task(self, bvid: str) -> str:
        """添加视频任务
        
        Args:
            bvid: 视频BV号
            
        Returns:
            str: 任务ID
        """
        try:
            # 获取视频信息
            video_info = await self.video_collector.get_video_info(bvid)
            
            # 创建任务
            task = await self.task_manager.create_task(video_info)
            
            self.logger.info(f"添加视频任务: {task['task_id']}")
            return task["task_id"]
        except Exception as e:
            self.logger.error(f"添加视频任务失败: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> str:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 任务状态
        """
        try:
            task = await self.database_manager.get_task_info(task_id)
            return task["status"]
        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            raise
    
    async def get_task_logs(self, task_id: str) -> list:
        """获取任务日志
        
        Args:
            task_id: 任务ID
            
        Returns:
            list: 任务日志列表
        """
        try:
            return await self.database_manager.get_task_logs(task_id)
        except Exception as e:
            self.logger.error(f"获取任务日志失败: {e}")
            raise
    
    async def get_video_info(self, bvid: str) -> Dict[str, Any]:
        """获取视频信息
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        try:
            return await self.database_manager.get_video_info(bvid)
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            raise
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            Dict[str, Any]: 存储统计信息
        """
        try:
            return await self.storage_manager.get_storage_stats()
        except Exception as e:
            self.logger.error(f"获取存储统计信息失败: {e}")
            raise
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态
        
        Returns:
            Dict[str, Any]: 系统状态
        """
        try:
            # 获取任务统计
            task_stats = await self.database_manager.get_task_stats()
            
            # 获取存储统计
            storage_stats = await self.storage_manager.get_storage_stats()
            
            return {
                "status": "running",
                "active_tasks": task_stats["active_count"],
                "completed_tasks": task_stats["completed_count"],
                "failed_tasks": task_stats["failed_count"],
                "storage": storage_stats
            }
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            raise
    
    async def process_video(self, video_info: Dict[str, Any]) -> bool:
        """处理单个视频
        
        Args:
            video_info: 视频信息
            
        Returns:
            bool: 是否处理成功
        """
        try:
            # 创建任务
            task = await self.task_manager.create_task(video_info)
            self.logger.info(f"创建任务: {task['task_id']}")
            
            # 更新任务状态
            await self.task_manager.update_task_status(task["task_id"], "processing")
            
            # 下载视频
            video_path = await self.video_collector.download_video(video_info["bvid"])
            await self.task_manager.update_task_progress(task["task_id"], 20)
            
            # 提取音频
            audio_path = await self.audio_processor.extract_audio(video_path)
            await self.task_manager.update_task_progress(task["task_id"], 40)
            
            # 语音识别
            transcript = await self.speech_recognizer.transcribe(audio_path)
            await self.task_manager.update_task_progress(task["task_id"], 60)
            
            # 生成Markdown
            markdown_path = await self.markdown_generator.generate(
                video_info,
                transcript
            )
            await self.task_manager.update_task_progress(task["task_id"], 80)
            
            # 更新任务状态
            await self.task_manager.update_task_status(task["task_id"], "completed")
            await self.task_manager.update_task_progress(task["task_id"], 100)
            
            # 清理临时文件
            await self.storage_manager.cleanup_old_files()
            
            return True
        except Exception as e:
            self.logger.error(f"处理视频失败: {e}")
            await self.task_manager.update_task_status(task["task_id"], "failed")
            return False
    
    async def run(self):
        """运行主程序"""
        try:
            # 启动系统
            await self.start()
            
            # 获取UP主视频列表
            mid = self.config["bilibili"]["up_mid"]
            videos = await self.video_collector.get_up_videos(mid)
            
            # 筛选视频
            filtered_videos = await self.video_filter.filter_videos(videos)
            self.logger.info(f"筛选出 {len(filtered_videos)} 个视频")
            
            # 处理视频
            for video in filtered_videos:
                await self.process_video(video)
            
            # 生成索引
            await self.markdown_generator.generate_index(filtered_videos)
            
            # 停止系统
            await self.stop()
            
            self.logger.info("程序运行完成")
        except Exception as e:
            self.logger.error(f"程序运行失败: {e}")
            raise

async def main():
    """主函数"""
    try:
        # 加载配置
        config_path = Path("config.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # 创建并运行系统
        automation = VMZWikiAutomation(config)
        await automation.run()
    except Exception as e:
        print(f"程序运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 