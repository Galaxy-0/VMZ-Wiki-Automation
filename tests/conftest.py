"""测试配置文件"""
import os
import pytest
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """测试数据目录"""
    return ROOT_DIR / "tests" / "fixtures"

@pytest.fixture
def config() -> Dict[str, Any]:
    """测试配置"""
    return {
        "bilibili": {
            "base_url": "https://api.bilibili.com",
            "timeout": 30,
            "retry_times": 3,
            "retry_delay": 1
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "format": "wav",
            "temp_dir": "tests/fixtures/temp"
        },
        "speech": {
            "model": "base",
            "language": "zh",
            "device": "cpu"
        },
        "markdown": {
            "template_dir": "tests/fixtures/templates",
            "output_dir": "tests/fixtures/output"
        },
        "storage": {
            "hot_storage": "tests/fixtures/hot",
            "cold_storage": "tests/fixtures/cold",
            "temp_storage": "tests/fixtures/temp",
            "min_free_space": 1024 * 1024 * 100,  # 100MB
            "max_hot_storage_age": 30  # 30天
        },
        "database": {
            "mongodb": {
                "uri": "mongodb://localhost:27017",
                "database": "vmz_wiki_test"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            }
        },
        "video_filter": {
            "time_range": {
                "start": (datetime.now() - timedelta(days=30)).isoformat(),
                "end": datetime.now().isoformat()
            },
            "duration_range": {
                "min": 60,  # 1分钟
                "max": 3600  # 1小时
            },
            "view_threshold": 1000,
            "like_threshold": 100,
            "keywords": ["测试", "示例"],
            "tags": ["教程", "编程"],
            "_test_mode": True  # 测试模式标志
        },
        "processing": {
            "max_workers": 4,
            "batch_size": 10,
            "retry_times": 3,
            "retry_delay": 5,
            "output_dir": "tests/fixtures/output",
            "template_dir": "tests/fixtures/templates"
        }
    }

@pytest.fixture
def mock_video_info() -> Dict[str, Any]:
    """模拟视频信息"""
    return {
        "code": 0,
        "data": {
            "bvid": "BV1xx411c7mD",
            "title": "测试视频",
            "desc": "这是一个测试视频",
            "duration": 300,
            "owner": {
                "mid": 123456,
                "name": "测试UP主"
            },
            "stat": {
                "view": 1000,
                "like": 100,
                "favorite": 200
            },
            "pubdate": 1704067200,
            "tags": [
                {"tag_name": "教程"},
                {"tag_name": "编程"}
            ]
        }
    }

@pytest.fixture
def mock_audio_file() -> str:
    """模拟音频文件路径"""
    return "tests/fixtures/audio/test.wav"

@pytest.fixture
def mock_transcript() -> Dict[str, Any]:
    """模拟转录文本"""
    return {
        "text": "这是一个测试视频的转录文本。",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.0,
                "text": "这是第一段文本"
            },
            {
                "id": 1,
                "start": 5.5,
                "end": 10.0,
                "text": "这是第二段文本"
            }
        ]
    }

@pytest.fixture
def mock_markdown_output() -> str:
    """模拟Markdown输出"""
    return """# 测试视频

## 视频信息
- 标题：测试视频
- UP主：测试UP主
- 时长：5分钟
- 播放量：1000
- 点赞数：100
- 收藏数：200

## 视频内容
这是一个测试视频的转录文本。
"""

@pytest.fixture
def mock_task() -> Dict[str, Any]:
    """模拟任务信息"""
    return {
        "task_id": "test_task_001",
        "bvid": "BV1xx411c7mD",
        "status": "pending",
        "priority": 1,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@pytest.fixture
def mock_storage_stats() -> Dict[str, Any]:
    """模拟存储统计信息"""
    return {
        "hot_storage": {
            "total_space": 1024 * 1024 * 1000,  # 1GB
            "used_space": 512 * 1024 * 1024,    # 512MB
            "file_count": 10
        },
        "cold_storage": {
            "total_space": 1024 * 1024 * 5000,  # 5GB
            "used_space": 1024 * 1024 * 2000,   # 2GB
            "file_count": 50
        },
        "temp_storage": {
            "total_space": 1024 * 1024 * 100,   # 100MB
            "used_space": 50 * 1024 * 1024,     # 50MB
            "file_count": 5
        }
    }

@pytest.fixture(autouse=True)
def setup_test_env():
    """设置测试环境"""
    # 创建测试目录
    os.makedirs("tests/fixtures/temp", exist_ok=True)
    os.makedirs("tests/fixtures/hot", exist_ok=True)
    os.makedirs("tests/fixtures/cold", exist_ok=True)
    os.makedirs("tests/fixtures/output", exist_ok=True)
    os.makedirs("tests/fixtures/templates", exist_ok=True)
    os.makedirs("tests/fixtures/audio", exist_ok=True)
    
    yield
    
    # 清理测试目录
    import shutil
    shutil.rmtree("tests/fixtures/temp", ignore_errors=True)
    shutil.rmtree("tests/fixtures/hot", ignore_errors=True)
    shutil.rmtree("tests/fixtures/cold", ignore_errors=True)
    shutil.rmtree("tests/fixtures/output", ignore_errors=True)

@pytest.fixture(scope="session")
def mock_video_file(test_data_dir: Path) -> Path:
    """模拟视频文件"""
    video_file = test_data_dir / "test_video.mp4"
    if not video_file.exists():
        # 创建一个空的视频文件用于测试
        video_file.parent.mkdir(parents=True, exist_ok=True)
        video_file.touch()
    return video_file 