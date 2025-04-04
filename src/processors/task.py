"""任务管理器模块"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from queue import PriorityQueue
import threading

@dataclass
class Task:
    """任务数据类"""
    task_id: str
    video_info: Dict[str, Any]
    status: str = "pending"
    priority: int = 1
    retry_count: int = 0
    progress: int = 0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class TaskManager:
    """任务管理器类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化任务管理器
        
        Args:
            config: 配置信息，包含并发数和批处理大小等参数
        """
        self.config = config
        self.max_concurrent_downloads = config.get("max_concurrent_downloads", 3)
        self.max_concurrent_processes = config.get("max_concurrent_processes", 2)
        self.batch_size = config.get("batch_size", 10)
        
        # 任务存储
        self.tasks: Dict[str, Task] = {}
        self.task_queue = PriorityQueue()
        self.lock = threading.Lock()
        
        # 任务状态统计
        self.status_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        }
    
    def add_task(self, video_info: Dict[str, Any]) -> str:
        """添加新任务
        
        Args:
            video_info: 视频信息
            
        Returns:
            str: 任务ID
        """
        with self.lock:
            task_id = str(uuid.uuid4())
            priority = video_info.get("priority", 1)
            
            task = Task(
                task_id=task_id,
                video_info=video_info,
                priority=priority
            )
            self.tasks[task_id] = task
            self.status_counts["pending"] += 1
            
            # 将任务添加到优先级队列
            # 注意：优先级队列是按照最小值优先，所以高优先级任务应该有更小的值
            # 使用负值来实现高数字 = 高优先级
            self.task_queue.put((-priority, task_id))
            
            return task_id
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[str]: 任务状态，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        return task.status if task else None
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            
        Returns:
            bool: 是否更新成功
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise Exception("任务不存在")
            
            # 更新状态计数
            self.status_counts[task.status] -= 1
            self.status_counts[status] += 1
            
            # 更新任务状态
            task.status = status
            task.updated_at = datetime.now()
            
            return True
    
    def get_next_batch(self) -> List[str]:
        """获取下一批待处理任务
        
        Returns:
            List[str]: 任务ID列表
        """
        with self.lock:
            batch = []
            seen_tasks = set()  # 使用集合追踪已处理的任务ID
            
            # 只处理队列中当前的任务，避免无限循环
            current_queue_size = self.task_queue.qsize()
            
            for _ in range(min(current_queue_size, self.batch_size * 2)):
                if len(batch) >= self.batch_size:
                    break
                
                if self.task_queue.empty():
                    break
                
                try:
                    neg_priority, task_id = self.task_queue.get(block=False)
                    
                    # 如果已经处理过这个任务ID，跳过
                    if task_id in seen_tasks:
                        continue
                    
                    seen_tasks.add(task_id)
                    task = self.tasks.get(task_id)
                    
                    if task and task.status == "pending":
                        batch.append(task_id)
                        self.update_task_status(task_id, "processing")
                    elif task:
                        # 放回队列
                        self.task_queue.put((neg_priority, task_id))
                except Exception:
                    # 如果队列操作失败，继续下一个
                    continue
            
            return batch
    
    def retry_failed_task(self, task_id: str) -> bool:
        """重试失败的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否重试成功
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise Exception("任务不存在")
            
            if task.status != "failed":
                raise Exception("只能重试失败的任务")
            
            # 重置任务状态
            task.status = "pending"
            task.retry_count += 1
            task.error = None
            task.updated_at = datetime.now()
            
            # 更新状态计数
            self.status_counts["failed"] -= 1
            self.status_counts["pending"] += 1
            
            # 重新加入队列，保持负优先级
            priority = task.priority
            self.task_queue.put((-priority, task_id))
            
            return True
    
    def update_task_progress(self, task_id: str, progress: int) -> bool:
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度值(0-100)
            
        Returns:
            bool: 是否更新成功
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise Exception("任务不存在")
            
            task.progress = max(0, min(100, progress))
            task.updated_at = datetime.now()
            
            return True
    
    def get_task_progress(self, task_id: str) -> int:
        """获取任务进度
        
        Args:
            task_id: 任务ID
            
        Returns:
            int: 进度值(0-100)
        """
        task = self.tasks.get(task_id)
        return task.progress if task else 0
    
    def update_task_error(self, task_id: str, error: str) -> bool:
        """更新任务错误信息
        
        Args:
            task_id: 任务ID
            error: 错误信息
            
        Returns:
            bool: 是否更新成功
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise Exception("任务不存在")
            
            task.error = error
            task.status = "failed"
            task.updated_at = datetime.now()
            
            # 更新状态计数
            self.status_counts["processing"] -= 1
            self.status_counts["failed"] += 1
            
            return True
    
    def get_task_error(self, task_id: str) -> Optional[str]:
        """获取任务错误信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[str]: 错误信息，如果任务不存在则返回None
        """
        task = self.tasks.get(task_id)
        return task.error if task else None
    
    def get_task_retry_count(self, task_id: str) -> int:
        """获取任务重试次数
        
        Args:
            task_id: 任务ID
            
        Returns:
            int: 重试次数
        """
        task = self.tasks.get(task_id)
        return task.retry_count if task else 0
    
    def cleanup_completed_tasks(self) -> int:
        """清理已完成的任务
        
        Returns:
            int: 清理的任务数量
        """
        with self.lock:
            completed_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.status == "completed"
            ]
            
            for task_id in completed_tasks:
                del self.tasks[task_id]
                self.status_counts["completed"] -= 1
            
            return len(completed_tasks)
    
    def get_task_stats(self) -> Dict[str, int]:
        """获取任务统计信息
        
        Returns:
            Dict[str, int]: 各状态的任务数量
        """
        return self.status_counts.copy() 