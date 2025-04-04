"""音频处理器模块"""
import os
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AudioProcessor:
    """音频处理器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化音频处理器
        
        Args:
            config: 配置信息，包含音频处理参数等
        """
        self.config = config
        self.ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
        self.output_dir = Path(config.get("output_dir", "output/audio"))
        self.segment_duration = config.get("segment_duration", 300)  # 5分钟
        self.max_workers = config.get("max_workers", 4)
        self.logger = logging.getLogger(__name__)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    async def extract_audio(self, video_path: str) -> str:
        """从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            str: 音频文件路径
        """
        video_path = Path(video_path)
        audio_path = self.output_dir / f"{video_path.stem}.wav"
        
        if audio_path.exists():
            self.logger.info(f"音频文件已存在: {audio_path}")
            return str(audio_path)
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vn",  # 不处理视频
            "-acodec", "pcm_s16le",  # 使用PCM编码
            "-ar", "16000",  # 采样率16kHz
            "-ac", "1",  # 单声道
            "-y",  # 覆盖已存在的文件
            str(audio_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"音频提取失败: {process.returncode}")
            
            return str(audio_path)
        except Exception as e:
            self.logger.error(f"音频提取失败: {e}")
            raise
    
    async def segment_audio(self, audio_path: str) -> List[str]:
        """将音频分割成小段
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            List[str]: 音频片段路径列表
        """
        audio_path = Path(audio_path)
        segment_dir = self.output_dir / audio_path.stem
        segment_dir.mkdir(exist_ok=True)
        
        # 获取音频时长
        duration = await self._get_audio_duration(audio_path)
        
        # 计算需要分割的片段数
        num_segments = (duration + self.segment_duration - 1) // self.segment_duration
        segment_paths = []
        
        # 分割音频
        for i in range(num_segments):
            start_time = i * self.segment_duration
            segment_path = segment_dir / f"segment_{i:03d}.wav"
            
            cmd = [
                self.ffmpeg_path,
                "-i", str(audio_path),
                "-ss", str(start_time),
                "-t", str(self.segment_duration),
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                str(segment_path)
            ]
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"音频分割失败: {process.returncode}")
                
                segment_paths.append(str(segment_path))
            except Exception as e:
                self.logger.error(f"音频分割失败: {e}")
                raise
        
        return segment_paths
    
    async def optimize_audio(self, audio_path: str) -> str:
        """优化音频质量
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            str: 优化后的音频文件路径
        """
        audio_path = Path(audio_path)
        optimized_path = self.output_dir / f"{audio_path.stem}_optimized.wav"
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(audio_path),
            "-af", "highpass=200,lowpass=3000,volume=2.0",  # 高通滤波、低通滤波、音量调整
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            str(optimized_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"音频优化失败: {process.returncode}")
            
            return str(optimized_path)
        except Exception as e:
            self.logger.error(f"音频优化失败: {e}")
            raise
    
    async def cleanup(self, audio_path: str) -> bool:
        """清理音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            bool: 是否清理成功
        """
        try:
            audio_path = Path(audio_path)
            if audio_path.exists():
                audio_path.unlink()
                self.logger.info(f"已清理音频文件: {audio_path}")
            return True
        except Exception as e:
            self.logger.error(f"清理音频文件失败: {e}")
            return False
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            float: 音频时长（秒）
        """
        cmd = [
            self.ffmpeg_path,
            "-i", str(audio_path),
            "-hide_banner"
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            # 从ffmpeg输出中提取时长信息
            for line in stderr.decode().split("\n"):
                if "Duration" in line:
                    time_str = line.split("Duration: ")[1].split(",")[0]
                    h, m, s = map(float, time_str.split(":"))
                    return h * 3600 + m * 60 + s
            
            raise Exception("无法获取音频时长")
        except Exception as e:
            self.logger.error(f"获取音频时长失败: {e}")
            raise 