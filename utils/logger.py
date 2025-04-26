import logging
import os
from datetime import datetime
from typing import Optional

class Logger:
    _instance: Optional['Logger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self) -> None:
        """Initialize logger with file and console handlers"""
        self.logger = logging.getLogger('QcctvKor')
        self.logger.setLevel(logging.DEBUG)
        
        # 로그 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 로그 파일 설정
        log_dir = os.path.join(os.path.expanduser('~'), '.qgis3', 'QcctvKor', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(
            log_dir,
            f"qcctvkor_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        # 파일 핸들러 추가
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Get logger instance"""
        if cls._instance is None:
            cls()
        return cls._instance.logger
    
    @staticmethod
    def format_error(error: Exception, context: str = "") -> str:
        """Format error message with context"""
        return f"{context} - {type(error).__name__}: {str(error)}"
    
    @staticmethod
    def log_function_call(func):
        """Decorator for logging function calls"""
        def wrapper(*args, **kwargs):
            logger = Logger.get_logger()
            func_name = func.__name__
            logger.debug(f"Calling {func_name}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Completed {func_name}")
                return result
            except Exception as e:
                logger.error(
                    Logger.format_error(e, f"Error in {func_name}")
                )
                raise
        return wrapper 