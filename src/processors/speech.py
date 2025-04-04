"""语音识别器模块"""
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import whisper
import torch

class SpeechRecognizer:
    """语音识别器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化语音识别器
        
        Args:
            config: 配置信息，包含模型参数等
        """
        self.config = config
        self.model_name = config.get("model_name", "base")
        self.device = config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        self.output_dir = Path(config.get("output_dir", "output/transcripts"))
        self.max_workers = config.get("max_workers", 4)
        self.logger = logging.getLogger(__name__)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 加载模型
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载Whisper模型"""
        try:
            self.logger.info(f"正在加载Whisper模型: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            self.logger.info("模型加载完成")
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            raise
    
    async def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """转录音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Dict[str, Any]: 转录结果
        """
        try:
            # 在线程池中运行转录任务
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._transcribe_audio_internal,
                audio_path
            )
            
            # 保存转录结果
            output_path = self._save_transcript(result, audio_path)
            
            return {
                "text": result["text"],
                "segments": result["segments"],
                "output_path": str(output_path)
            }
        except Exception as e:
            self.logger.error(f"音频转录失败: {e}")
            raise
    
    async def transcribe_batch(self, audio_paths: List[str]) -> List[Dict[str, Any]]:
        """批量转录音频文件
        
        Args:
            audio_paths: 音频文件路径列表
            
        Returns:
            List[Dict[str, Any]]: 转录结果列表
        """
        tasks = [self.transcribe_audio(path) for path in audio_paths]
        return await asyncio.gather(*tasks)
    
    def _transcribe_audio_internal(self, audio_path: str) -> Dict[str, Any]:
        """内部转录方法（在线程池中运行）
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Dict[str, Any]: 转录结果
        """
        try:
            result = self.model.transcribe(
                audio_path,
                language="zh",  # 中文
                task="transcribe",
                fp16=False
            )
            return result
        except Exception as e:
            self.logger.error(f"音频转录失败: {e}")
            raise
    
    def _save_transcript(self, result: Dict[str, Any], audio_path: str) -> Path:
        """保存转录结果
        
        Args:
            result: 转录结果
            audio_path: 音频文件路径
            
        Returns:
            Path: 输出文件路径
        """
        audio_path = Path(audio_path)
        output_path = self.output_dir / f"{audio_path.stem}.json"
        
        try:
            import json
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return output_path
        except Exception as e:
            self.logger.error(f"保存转录结果失败: {e}")
            raise
    
    def post_process_transcript(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """后处理转录结果
        
        Args:
            transcript: 原始转录结果
            
        Returns:
            Dict[str, Any]: 处理后的转录结果
        """
        try:
            # 合并短句
            merged_segments = []
            current_segment = None
            
            for segment in transcript["segments"]:
                if current_segment is None:
                    current_segment = segment.copy()
                else:
                    # 如果当前片段与下一个片段间隔小于1秒，则合并
                    if segment["start"] - current_segment["end"] < 1.0:
                        current_segment["text"] += " " + segment["text"]
                        current_segment["end"] = segment["end"]
                    else:
                        merged_segments.append(current_segment)
                        current_segment = segment.copy()
            
            if current_segment is not None:
                merged_segments.append(current_segment)
            
            # 更新转录结果
            transcript["segments"] = merged_segments
            transcript["text"] = " ".join(segment["text"] for segment in merged_segments)
            
            return transcript
        except Exception as e:
            self.logger.error(f"转录结果后处理失败: {e}")
            raise
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.model is not None:
                del self.model
                torch.cuda.empty_cache()
            self.executor.shutdown()
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}") 