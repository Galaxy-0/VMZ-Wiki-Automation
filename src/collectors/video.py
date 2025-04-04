"""视频采集器模块"""
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from urllib.parse import urlencode
from pathlib import Path
import os

class VideoCollector:
    """视频采集器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化视频采集器
        
        Args:
            config: 配置信息，包含API密钥和请求参数等
        """
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.bilibili.com")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.logger = logging.getLogger(__name__)
    
    async def get_video_info(self, bvid: str) -> Dict[str, Any]:
        """获取视频信息
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        url = f"{self.base_url}/x/web-interface/view"
        params = {"bvid": bvid}
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"获取视频信息失败: {response.status}")
                
                data = await response.json()
                if data["code"] != 0:
                    raise Exception(f"获取视频信息失败: {data['message']}")
                
                return self._parse_video_info(data["data"])
    
    async def get_up_videos(self, mid: int, page: int = 1, page_size: int = 30) -> List[Dict[str, Any]]:
        """获取UP主视频列表
        
        Args:
            mid: UP主ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            List[Dict[str, Any]]: 视频列表
        """
        url = f"{self.base_url}/x/space/arc/search"
        params = {
            "mid": mid,
            "page": page,
            "page_size": page_size,
            "order": "pubdate"
        }
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"获取UP主视频列表失败: {response.status}")
                
                data = await response.json()
                if data["code"] != 0:
                    raise Exception(f"获取UP主视频列表失败: {data['message']}")
                
                return [self._parse_video_info(video) for video in data["data"]["list"]["vlist"]]
    
    async def get_video_download_url(self, bvid: str) -> str:
        """获取视频下载地址
        
        Args:
            bvid: 视频BV号
            
        Returns:
            str: 下载地址
        """
        url = f"{self.base_url}/x/player/playurl"
        params = {
            "bvid": bvid,
            "cid": await self._get_video_cid(bvid),
            "qn": 80,  # 清晰度
            "type": "mp4"
        }
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"获取视频下载地址失败: {response.status}")
                
                data = await response.json()
                if data["code"] != 0:
                    raise Exception(f"获取视频下载地址失败: {data['message']}")
                
                return data["data"]["durl"][0]["url"]
    
    async def download_video(self, bvid: str) -> Path:
        """下载视频
        
        Args:
            bvid: 视频BV号
            
        Returns:
            Path: 视频文件路径
        """
        try:
            # 获取下载地址
            download_url = await self.get_video_download_url(bvid)
            
            # 创建下载目录
            download_dir = Path("data/videos")
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            filename = f"{bvid}.mp4"
            filepath = download_dir / filename
            
            # 如果文件已存在，直接返回
            if filepath.exists():
                self.logger.info(f"视频文件已存在: {filepath}")
                return filepath
            
            # 下载视频
            self.logger.info(f"开始下载视频: {bvid}")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(download_url) as response:
                    if response.status != 200:
                        raise Exception(f"下载视频失败: {response.status}")
                    
                    # 获取文件大小
                    total_size = int(response.headers.get("content-length", 0))
                    
                    # 写入文件
                    with open(filepath, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            self.logger.info(f"视频下载完成: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"下载视频失败: {e}")
            raise
    
    async def _get_video_cid(self, bvid: str) -> int:
        """获取视频CID
        
        Args:
            bvid: 视频BV号
            
        Returns:
            int: 视频CID
        """
        url = f"{self.base_url}/x/web-interface/view"
        params = {"bvid": bvid}
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"获取视频CID失败: {response.status}")
                
                data = await response.json()
                if data["code"] != 0:
                    raise Exception(f"获取视频CID失败: {data['message']}")
                
                return data["data"]["cid"]
    
    def _parse_video_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析视频信息
        
        Args:
            data: 原始视频信息
            
        Returns:
            Dict[str, Any]: 解析后的视频信息
        """
        return {
            "bvid": data.get("bvid"),
            "title": data.get("title"),
            "description": data.get("desc"),
            "duration": data.get("duration"),
            "view_count": data.get("stat", {}).get("view"),
            "like_count": data.get("stat", {}).get("like"),
            "coin_count": data.get("stat", {}).get("coin"),
            "favorite_count": data.get("stat", {}).get("favorite"),
            "share_count": data.get("stat", {}).get("share"),
            "pubdate": datetime.fromtimestamp(data.get("pubdate", 0)),
            "tags": [tag["tag_name"] for tag in data.get("tags", [])],
            "owner": {
                "mid": data.get("owner", {}).get("mid"),
                "name": data.get("owner", {}).get("name"),
                "face": data.get("owner", {}).get("face")
            }
        } 