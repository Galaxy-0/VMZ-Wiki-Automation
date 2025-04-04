"""视频采集器单元测试"""
import pytest
from typing import Dict, Any
import aiohttp
from src.collectors.video import VideoCollector

@pytest.fixture
def video_collector(config: Dict[str, Any]) -> VideoCollector:
    """视频采集器实例"""
    return VideoCollector(config["bilibili"])

@pytest.mark.asyncio
async def test_video_collector_initialization(video_collector: VideoCollector):
    """测试视频采集器初始化"""
    assert video_collector is not None
    assert video_collector.base_url == "https://api.bilibili.com"
    assert video_collector.config["timeout"] == 30

class MockResponse:
    def __init__(self, status=200, json_data=None):
        self.status = status
        self._json_data = json_data or {}
    
    async def json(self):
        return self._json_data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockClientSession:
    def __init__(self, headers=None):
        self.headers = headers
        self.response = None
    
    def set_response(self, response):
        self.response = response
        return self
        
    def get(self, url, params=None):
        return self.response
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_get_video_info(monkeypatch, video_collector: VideoCollector, mock_video_info: Dict[str, Any]):
    """测试获取视频信息"""
    # 准备模拟的响应
    mock_response = MockResponse(json_data=mock_video_info)
    
    # 创建一个替换原始 ClientSession 的类
    orig_init = aiohttp.ClientSession.__init__
    
    def mock_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.get = lambda url, params=None: mock_response
    
    # 替换 aiohttp.ClientSession.__init__
    monkeypatch.setattr(aiohttp.ClientSession, "__init__", mock_init)
    
    # 模拟视频解析
    def mock_parse_video_info(data):
        return {
            "bvid": "BV1xx411c7mD",
            "title": "测试视频"
        }
    
    monkeypatch.setattr(video_collector, "_parse_video_info", mock_parse_video_info)
    
    result = await video_collector.get_video_info("BV1xx411c7mD")
    assert result["bvid"] == "BV1xx411c7mD"

@pytest.mark.asyncio
async def test_get_up_videos(monkeypatch, video_collector: VideoCollector):
    """测试获取UP主视频列表"""
    # 准备模拟的响应
    mock_response = MockResponse(json_data={
        "code": 0,
        "data": {
            "list": {
                "vlist": [
                    {
                        "bvid": "BV1xx411c7mD",
                        "title": "测试视频1",
                        "created": 1704067200,
                        "length": "05:00",
                        "play": 1000,
                        "video_review": 100,
                        "favorites": 200
                    }
                ]
            }
        }
    })
    
    # 创建一个替换原始 ClientSession 的类
    orig_init = aiohttp.ClientSession.__init__
    
    def mock_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.get = lambda url, params=None: mock_response
    
    # 替换 aiohttp.ClientSession.__init__
    monkeypatch.setattr(aiohttp.ClientSession, "__init__", mock_init)
    
    # 模拟视频解析
    def mock_parse_video_info(data):
        return {
            "bvid": data["bvid"],
            "title": data["title"]
        }
    
    monkeypatch.setattr(video_collector, "_parse_video_info", mock_parse_video_info)
    
    result = await video_collector.get_up_videos("123456")
    assert len(result) == 1
    assert result[0]["bvid"] == "BV1xx411c7mD"

@pytest.mark.asyncio
async def test_parse_video_info(video_collector: VideoCollector):
    """测试解析视频信息"""
    raw_info = {
        "bvid": "BV1xx411c7mD",
        "title": "测试视频",
        "created": 1704067200,
        "length": "05:00",
        "play": 1000,
        "video_review": 100,
        "favorites": 200,
        "duration": 300,
        "stat": {
            "view": 1000,
            "like": 100
        }
    }
    
    result = video_collector._parse_video_info(raw_info)
    assert result["bvid"] == "BV1xx411c7mD"
    assert result["title"] == "测试视频"
    assert result["duration"] == 300  # 直接使用原始数据的 duration

@pytest.mark.asyncio
async def test_get_video_download_url(monkeypatch, video_collector: VideoCollector):
    """测试获取视频下载地址"""
    # 模拟获取 CID
    async def mock_get_video_cid(bvid):
        return 12345
    
    monkeypatch.setattr(video_collector, "_get_video_cid", mock_get_video_cid)
    
    # 准备模拟的响应
    mock_response = MockResponse(json_data={
        "code": 0,
        "data": {
            "durl": [
                {
                    "url": "https://example.com/video.mp4",
                    "size": 1024 * 1024 * 100,
                    "length": 300,
                    "order": 1
                }
            ]
        }
    })
    
    # 创建一个替换原始 ClientSession 的类
    orig_init = aiohttp.ClientSession.__init__
    
    def mock_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.get = lambda url, params=None: mock_response
    
    # 替换 aiohttp.ClientSession.__init__
    monkeypatch.setattr(aiohttp.ClientSession, "__init__", mock_init)
    
    result = await video_collector.get_video_download_url("BV1xx411c7mD")
    assert result == "https://example.com/video.mp4"

@pytest.mark.asyncio
async def test_error_handling(monkeypatch, video_collector: VideoCollector):
    """测试错误处理"""
    # 准备模拟的错误响应
    mock_response = MockResponse(status=200, json_data={
        "code": -404,
        "message": "视频不存在"
    })
    
    # 创建一个替换原始 ClientSession 的类
    orig_init = aiohttp.ClientSession.__init__
    
    def mock_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.get = lambda url, params=None: mock_response
    
    # 替换 aiohttp.ClientSession.__init__
    monkeypatch.setattr(aiohttp.ClientSession, "__init__", mock_init)
    
    with pytest.raises(Exception) as exc_info:
        await video_collector.get_video_info("invalid_bvid")
    assert "视频不存在" in str(exc_info.value) 