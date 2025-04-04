"""数据库管理器模块"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import motor.motor_asyncio
from pymongo import ASCENDING, DESCENDING
import redis.asyncio as redis
import json

class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化数据库管理器
        
        Args:
            config: 配置信息，包含数据库连接参数等
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # MongoDB配置
        self.mongo_uri = config.get("mongo_uri", "mongodb://localhost:27017")
        self.mongo_db = config.get("mongo_db", "vmz_wiki")
        self.mongo_client = None
        
        # Redis配置
        self.redis_uri = config.get("redis_uri", "redis://localhost:6379")
        self.redis_db = config.get("redis_db", 0)
        self.redis_client = None
    
    async def connect(self):
        """连接数据库"""
        try:
            # 连接MongoDB
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
            self.mongo_db = self.mongo_client[self.mongo_db]
            
            # 创建索引
            await self._create_indexes()
            
            # 连接Redis
            self.redis_client = await redis.from_url(
                self.redis_uri,
                db=self.redis_db,
                decode_responses=True
            )
            
            self.logger.info("数据库连接成功")
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        try:
            if self.mongo_client:
                self.mongo_client.close()
            if self.redis_client:
                await self.redis_client.close()
            self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"断开数据库连接失败: {e}")
    
    async def _create_indexes(self):
        """创建数据库索引"""
        try:
            # 视频信息索引
            await self.mongo_db.videos.create_index([("bvid", ASCENDING)], unique=True)
            await self.mongo_db.videos.create_index([("pubdate", DESCENDING)])
            await self.mongo_db.videos.create_index([("view_count", DESCENDING)])
            
            # 任务索引
            await self.mongo_db.tasks.create_index([("task_id", ASCENDING)], unique=True)
            await self.mongo_db.tasks.create_index([("status", ASCENDING)])
            await self.mongo_db.tasks.create_index([("created_at", DESCENDING)])
            
            # 存储统计索引
            await self.mongo_db.storage_stats.create_index([("timestamp", DESCENDING)])
        except Exception as e:
            self.logger.error(f"创建数据库索引失败: {e}")
            raise
    
    async def save_video_info(self, video_info: Dict[str, Any]) -> bool:
        """保存视频信息
        
        Args:
            video_info: 视频信息
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 添加更新时间
            video_info["updated_at"] = datetime.now()
            
            # 更新或插入视频信息
            await self.mongo_db.videos.update_one(
                {"bvid": video_info["bvid"]},
                {"$set": video_info},
                upsert=True
            )
            
            # 缓存视频信息
            await self.redis_client.setex(
                f"video:{video_info['bvid']}",
                3600,  # 1小时过期
                json.dumps(video_info, default=str)
            )
            
            return True
        except Exception as e:
            self.logger.error(f"保存视频信息失败: {e}")
            return False
    
    async def get_video_info(self, bvid: str) -> Optional[Dict[str, Any]]:
        """获取视频信息
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Optional[Dict[str, Any]]: 视频信息
        """
        try:
            # 尝试从缓存获取
            cached = await self.redis_client.get(f"video:{bvid}")
            if cached:
                return json.loads(cached)
            
            # 从数据库获取
            video_info = await self.mongo_db.videos.find_one({"bvid": bvid})
            if video_info:
                # 缓存视频信息
                await self.redis_client.setex(
                    f"video:{bvid}",
                    3600,
                    json.dumps(video_info, default=str)
                )
            
            return video_info
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            return None
    
    async def update_video_status(self, bvid: str, status: str) -> bool:
        """更新视频状态
        
        Args:
            bvid: 视频BV号
            status: 新状态
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 更新数据库
            result = await self.mongo_db.videos.update_one(
                {"bvid": bvid},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                # 清除缓存
                await self.redis_client.delete(f"video:{bvid}")
            
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"更新视频状态失败: {e}")
            return False
    
    async def save_task(self, task: Dict[str, Any]) -> bool:
        """保存任务信息
        
        Args:
            task: 任务信息
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 添加更新时间
            task["updated_at"] = datetime.now()
            
            # 更新或插入任务信息
            await self.mongo_db.tasks.update_one(
                {"task_id": task["task_id"]},
                {"$set": task},
                upsert=True
            )
            
            return True
        except Exception as e:
            self.logger.error(f"保存任务信息失败: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务信息
        """
        try:
            return await self.mongo_db.tasks.find_one({"task_id": task_id})
        except Exception as e:
            self.logger.error(f"获取任务信息失败: {e}")
            return None
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            
        Returns:
            bool: 是否更新成功
        """
        try:
            result = await self.mongo_db.tasks.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"更新任务状态失败: {e}")
            return False
    
    async def save_storage_stats(self, stats: Dict[str, Any]) -> bool:
        """保存存储统计信息
        
        Args:
            stats: 存储统计信息
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 添加时间戳
            stats["timestamp"] = datetime.now()
            
            # 插入统计信息
            await self.mongo_db.storage_stats.insert_one(stats)
            return True
        except Exception as e:
            self.logger.error(f"保存存储统计信息失败: {e}")
            return False
    
    async def get_latest_storage_stats(self) -> Optional[Dict[str, Any]]:
        """获取最新的存储统计信息
        
        Returns:
            Optional[Dict[str, Any]]: 存储统计信息
        """
        try:
            return await self.mongo_db.storage_stats.find_one(
                sort=[("timestamp", DESCENDING)]
            )
        except Exception as e:
            self.logger.error(f"获取存储统计信息失败: {e}")
            return None 