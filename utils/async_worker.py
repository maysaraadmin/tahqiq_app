"""
Async worker utilities for background operations
"""
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)

class AsyncWorker(QObject):
    """Base class for async operations"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    
    def __init__(self):
        super().__init__()
        self._is_running = False
    
    def is_running(self):
        """Check if worker is currently running"""
        return self._is_running
    
    def run(self):
        """Override this method in subclasses"""
        self._is_running = True
        try:
            self.execute()
            self.finished.emit(self.result)
        except Exception as e:
            logger.error(f"Async worker error: {e}")
            self.error.emit(str(e))
        finally:
            self._is_running = False

class LoadDataWorker(AsyncWorker):
    """Worker for loading data asynchronously"""
    def __init__(self, controller, method_name, *args, **kwargs):
        super().__init__()
        self.controller = controller
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
    
    def execute(self):
        """Execute the specified method"""
        method = getattr(self.controller, self.method_name)
        if method:
            return method(*self.args, **self.kwargs)
        else:
            raise AttributeError(f"Method {self.method_name} not found")

class DatabaseOperationWorker(AsyncWorker):
    """Worker for database operations"""
    def __init__(self, controller, operation, *args, **kwargs):
        super().__init__()
        self.controller = controller
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
    
    def execute(self):
        """Execute database operation"""
        try:
            result = self.operation(*self.args, **self.kwargs)
            logger.info(f"Database operation completed: {self.operation.__name__}")
            return result
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
