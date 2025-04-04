"""视频筛选器单元测试"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from src.filters.video import VideoFilter

@pytest.fixture
def video_filter(config: Dict[str, Any]):
    """视频筛选器实例"""
    return VideoFilter(config["video_filter"])

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
        "tags": ["测试", "示例"]
    }

def test_video_filter_initialization(video_filter: VideoFilter):
    """测试视频筛选器初始化"""
    assert video_filter is not None
    assert video_filter.start_date is None
    assert video_filter.end_date is None
    assert video_filter.min_duration is None
    assert video_filter.max_duration is None
    assert video_filter.min_views is None
    assert video_filter.min_likes is None
    assert video_filter.exclude_keywords == []
    assert video_filter.include_keywords == []
    assert video_filter.exclude_tags == []
    assert video_filter.include_tags == []
    assert video_filter.custom_rules == []

def test_set_time_range(video_filter: VideoFilter):
    """测试设置时间范围"""
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    video_filter.set_time_range(start_date, end_date)
    assert video_filter.start_date == start_date
    assert video_filter.end_date == end_date

def test_set_duration_range(video_filter: VideoFilter):
    """测试设置时长范围"""
    min_duration = 300  # 5分钟
    max_duration = 3600  # 1小时
    
    video_filter.set_duration_range(min_duration, max_duration)
    assert video_filter.min_duration == min_duration
    assert video_filter.max_duration == max_duration

def test_set_view_like_thresholds(video_filter: VideoFilter):
    """测试设置播放量和点赞数阈值"""
    min_views = 1000
    min_likes = 100
    
    video_filter.set_view_like_thresholds(min_views, min_likes)
    assert video_filter.min_views == min_views
    assert video_filter.min_likes == min_likes

def test_set_keywords(video_filter: VideoFilter):
    """测试设置关键词"""
    exclude_keywords = ["直播回放", "预告"]
    include_keywords = ["教程", "讲解"]
    
    video_filter.set_keywords(exclude_keywords, include_keywords)
    assert video_filter.exclude_keywords == exclude_keywords
    assert video_filter.include_keywords == include_keywords

def test_set_tags(video_filter: VideoFilter):
    """测试设置标签"""
    exclude_tags = ["直播"]
    include_tags = ["技术", "编程"]
    
    video_filter.set_tags(exclude_tags, include_tags)
    assert video_filter.exclude_tags == exclude_tags
    assert video_filter.include_tags == include_tags

def test_add_custom_rule(video_filter: VideoFilter):
    """测试添加自定义规则"""
    def custom_rule(video_info: Dict[str, Any]) -> bool:
        return video_info["view_count"] > 5000
    
    video_filter.add_custom_rule(custom_rule)
    assert len(video_filter.custom_rules) == 1
    assert video_filter.custom_rules[0] == custom_rule

def test_filter_video(video_filter: VideoFilter, mock_video_info: Dict[str, Any]):
    """测试视频筛选"""
    # 设置筛选条件
    video_filter.set_duration_range(200, 400)
    video_filter.set_view_like_thresholds(500, 50)
    video_filter.set_keywords(["直播"], ["教程"])
    video_filter.set_tags(["直播"], ["技术"])
    
    # 测试符合条件的视频
    assert video_filter.filter_video(mock_video_info) is True
    
    # 测试不符合条件的视频
    mock_video_info["duration"] = 100
    assert video_filter.filter_video(mock_video_info) is False

def test_filter_batch(video_filter: VideoFilter):
    """测试批量视频筛选"""
    # 创建测试视频列表
    videos = [
        {
            "bvid": f"BV{i}",
            "title": f"视频{i}",
            "duration": 300,
            "view_count": 1000,
            "like_count": 100,
            "tags": ["技术"]
        }
        for i in range(5)
    ]
    
    # 设置筛选条件
    video_filter.set_duration_range(200, 400)
    video_filter.set_view_like_thresholds(500, 50)
    video_filter.set_tags([], ["技术"])
    
    # 批量筛选
    filtered_videos = video_filter.filter_batch(videos)
    
    # 验证结果
    assert len(filtered_videos) == 5
    assert all(video["duration"] >= 200 for video in filtered_videos)
    assert all(video["duration"] <= 400 for video in filtered_videos)
    assert all(video["view_count"] >= 500 for video in filtered_videos)
    assert all(video["like_count"] >= 50 for video in filtered_videos)
    assert all("技术" in video["tags"] for video in filtered_videos)

def test_custom_rule_filtering(video_filter: VideoFilter, mock_video_info: Dict[str, Any]):
    """测试自定义规则筛选"""
    # 添加自定义规则
    def high_quality_rule(video_info: Dict[str, Any]) -> bool:
        return video_info["view_count"] > 5000 and video_info["like_count"] > 500
    
    video_filter.add_custom_rule(high_quality_rule)
    
    # 测试高质量视频
    mock_video_info["view_count"] = 6000
    mock_video_info["like_count"] = 600
    assert video_filter.filter_video(mock_video_info) is True
    
    # 测试低质量视频
    mock_video_info["view_count"] = 4000
    mock_video_info["like_count"] = 400
    assert video_filter.filter_video(mock_video_info) is False

def test_error_handling(video_filter: VideoFilter):
    """测试错误处理"""
    # 测试无效的时间范围
    with pytest.raises(ValueError) as exc_info:
        video_filter.set_time_range(
            datetime.now(),
            datetime.now() - timedelta(days=1)
        )
    assert "结束时间必须晚于开始时间" in str(exc_info.value)
    
    # 测试无效的时长范围
    with pytest.raises(ValueError) as exc_info:
        video_filter.set_duration_range(400, 300)
    assert "最大时长必须大于最小时长" in str(exc_info.value)
    
    # 测试无效的阈值
    with pytest.raises(ValueError) as exc_info:
        video_filter.set_view_like_thresholds(-100, 50)
    assert "播放量和点赞数阈值必须大于0" in str(exc_info.value) 