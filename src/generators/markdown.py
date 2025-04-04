"""Markdown生成器模块"""
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json
from jinja2 import Environment, FileSystemLoader

class MarkdownGenerator:
    """Markdown生成器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Markdown生成器
        
        Args:
            config: 配置信息，包含模板路径等
        """
        self.config = config
        self.template_dir = Path(config.get("template_dir", "templates"))
        self.output_dir = Path(config.get("output_dir", "output/markdown"))
        self.logger = logging.getLogger(__name__)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate_markdown(self, video_info: Dict[str, Any], transcript: Dict[str, Any]) -> str:
        """生成Markdown文档
        
        Args:
            video_info: 视频信息
            transcript: 转录结果
            
        Returns:
            str: 生成的Markdown内容
        """
        try:
            # 准备模板数据
            template_data = {
                "video": video_info,
                "transcript": transcript,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 渲染模板
            template = self.env.get_template("video.md.j2")
            markdown_content = template.render(**template_data)
            
            return markdown_content
        except Exception as e:
            self.logger.error(f"生成Markdown文档失败: {e}")
            raise
    
    def save_markdown(self, content: str, video_info: Dict[str, Any]) -> str:
        """保存Markdown文档
        
        Args:
            content: Markdown内容
            video_info: 视频信息
            
        Returns:
            str: 保存的文件路径
        """
        try:
            # 生成文件名
            bvid = video_info.get("bvid", "unknown")
            title = video_info.get("title", "untitled")
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
            filename = f"{bvid}_{safe_title}.md"
            
            # 保存文件
            output_path = self.output_dir / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return str(output_path)
        except Exception as e:
            self.logger.error(f"保存Markdown文档失败: {e}")
            raise
    
    def format_timestamp(self, seconds: float) -> str:
        """格式化时间戳
        
        Args:
            seconds: 秒数
            
        Returns:
            str: 格式化的时间戳 (HH:MM:SS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def format_duration(self, seconds: float) -> str:
        """格式化时长
        
        Args:
            seconds: 秒数
            
        Returns:
            str: 格式化的时长
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
    
    def generate_batch(self, videos: List[Dict[str, Any]], transcripts: List[Dict[str, Any]]) -> List[str]:
        """批量生成Markdown文档
        
        Args:
            videos: 视频信息列表
            transcripts: 转录结果列表
            
        Returns:
            List[str]: 生成的文件路径列表
        """
        output_paths = []
        for video, transcript in zip(videos, transcripts):
            try:
                content = self.generate_markdown(video, transcript)
                output_path = self.save_markdown(content, video)
                output_paths.append(output_path)
            except Exception as e:
                self.logger.error(f"处理视频 {video.get('bvid')} 失败: {e}")
                continue
        return output_paths
    
    def generate_index(self, videos: List[Dict[str, Any]]) -> str:
        """生成索引文档
        
        Args:
            videos: 视频信息列表
            
        Returns:
            str: 索引文档路径
        """
        try:
            # 准备模板数据
            template_data = {
                "videos": videos,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 渲染模板
            template = self.env.get_template("index.md.j2")
            content = template.render(**template_data)
            
            # 保存文件
            output_path = self.output_dir / "index.md"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return str(output_path)
        except Exception as e:
            self.logger.error(f"生成索引文档失败: {e}")
            raise 