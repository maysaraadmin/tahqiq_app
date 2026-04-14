"""
Performance monitoring utilities for the Tahqiq application.
Provides tools for monitoring application performance and resource usage.
"""

import time
import psutil
import logging
from functools import wraps
from typing import Callable, Any, Dict
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Container for performance metrics"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_before = None
        self.memory_after = None
        self.cpu_before = None
        self.cpu_after = None
    
    @property
    def duration(self) -> float:
        """Get execution duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def memory_usage(self) -> float:
        """Get memory usage difference in MB"""
        if self.memory_before and self.memory_after:
            return self.memory_after - self.memory_before
        return 0.0
    
    @property
    def cpu_usage(self) -> float:
        """Get CPU usage difference"""
        if self.cpu_before is not None and self.cpu_after is not None:
            return self.cpu_after - self.cpu_before
        return 0.0

def monitor_performance(func: Callable) -> Callable:
    """
    Decorator to monitor function performance
    
    Args:
        func: Function to monitor
    
    Returns:
        Wrapped function with performance monitoring
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        metrics = PerformanceMetrics()
        
        # Record start metrics
        metrics.start_time = time.time()
        process = psutil.Process()
        metrics.memory_before = process.memory_info().rss / 1024 / 1024  # MB
        metrics.cpu_before = process.cpu_percent()
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Record end metrics
            metrics.end_time = time.time()
            metrics.memory_after = process.memory_info().rss / 1024 / 1024  # MB
            metrics.cpu_after = process.cpu_percent()
            
            # Log performance data
            logger.info(f"Performance metrics for {func.__name__}: "
                       f"duration={metrics.duration:.3f}s, "
                       f"memory={metrics.memory_usage:.2f}MB, "
                       f"cpu={metrics.cpu_usage:.1f}%")
            
            return result
            
        except Exception as e:
            # Log error with performance context
            logger.error(f"Error in {func.__name__} after {time.time() - metrics.start_time:.3f}s: {e}")
            raise
    
    return wrapper

class PerformanceMonitor(QObject):
    """Real-time performance monitor for Qt applications"""
    
    performance_update = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.is_monitoring = False
        self.update_interval = 1.0  # seconds
        
    def start_monitoring(self):
        """Start performance monitoring"""
        self.is_monitoring = True
        logger.info("Performance monitoring started")
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        logger.info("Performance monitoring stopped")
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            process = psutil.Process()
            
            return {
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'system_memory_percent': psutil.virtual_memory().percent,
                'system_cpu_percent': psutil.cpu_percent()
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def log_system_resources():
    """Log current system resource usage"""
    try:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        
        logger.info(f"System resources - Memory: {memory.percent}% used, "
                   f"CPU: {cpu}% used, "
                   f"Available: {memory.available / 1024 / 1024 / 1024:.1f}GB")
    except Exception as e:
        logger.error(f"Failed to log system resources: {e}")

def check_memory_usage(threshold_mb: float = 500.0) -> bool:
    """
    Check if memory usage exceeds threshold
    
    Args:
        threshold_mb: Memory threshold in MB
        
    Returns:
        True if memory usage exceeds threshold
    """
    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > threshold_mb:
            logger.warning(f"High memory usage detected: {memory_mb:.2f}MB > {threshold_mb}MB")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Failed to check memory usage: {e}")
        return False

def optimize_performance():
    """Optimize application performance"""
    try:
        # Force garbage collection
        import gc
        collected = gc.collect()
        
        # Log optimization results
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        logger.info(f"Performance optimization completed: "
                   f"collected {collected} objects, "
                   f"current memory: {memory_mb:.2f}MB")
        
        return collected
    except Exception as e:
        logger.error(f"Failed to optimize performance: {e}")
        return 0
