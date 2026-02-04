"""
日志模块
统一的日志记录
"""
import logging
import os
from datetime import datetime
import pytz


class BeijingTimeFormatter(logging.Formatter):
    """北京时间格式化器"""

    def formatTime(self, record, datefmt=None):
        """使用北京时间格式化时间戳"""
        china_tz = pytz.timezone('Asia/Shanghai')
        dt = datetime.fromtimestamp(record.created, tz=china_tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S')


class Logger:
    """日志管理器"""

    _logger = None

    @classmethod
    def get_logger(cls, name: str = 'crawler', log_dir: str = 'logs') -> logging.Logger:
        """
        获取日志记录器

        Args:
            name: 日志记录器名称
            log_dir: 日志目录

        Returns:
            logging.Logger 对象
        """
        if cls._logger is not None:
            return cls._logger

        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)

        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # 移除已有的处理器
        logger.handlers.clear()

        # 日志格式（使用北京时间）
        formatter = BeijingTimeFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 文件处理器（每天一个日志文件，使用北京时间）
        china_tz = pytz.timezone('Asia/Shanghai')
        beijing_now = datetime.now(china_tz)
        log_file = os.path.join(log_dir, f'crawler_{beijing_now.strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        cls._logger = logger
        return logger

    @classmethod
    def info(cls, message: str):
        """记录信息日志"""
        logger = cls.get_logger()
        logger.info(message)

    @classmethod
    def debug(cls, message: str):
        """记录调试日志"""
        logger = cls.get_logger()
        logger.debug(message)

    @classmethod
    def warning(cls, message: str):
        """记录警告日志"""
        logger = cls.get_logger()
        logger.warning(message)

    @classmethod
    def error(cls, message: str):
        """记录错误日志"""
        logger = cls.get_logger()
        logger.error(message)

    @classmethod
    def critical(cls, message: str):
        """记录严重错误日志"""
        logger = cls.get_logger()
        logger.critical(message)
