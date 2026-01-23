"""
时间工具模块
判断交易时段、工作日等
"""
from datetime import datetime, time
from typing import Tuple
import pytz


class TimeUtils:
    """时间工具类"""

    # 中国时区
    CHINA_TZ = pytz.timezone('Asia/Shanghai')

    # 交易时段
    MORNING_START = time(9, 30)   # 上午开盘
    MORNING_END = time(11, 30)    # 上午收盘
    AFTERNOON_START = time(13, 0) # 下午开盘
    AFTERNOON_END = time(15, 0)   # 下午收盘

    @classmethod
    def get_china_time(cls) -> datetime:
        """
        获取中国时区的当前时间

        Returns:
            中国时区的 datetime 对象
        """
        return datetime.now(cls.CHINA_TZ)

    @classmethod
    def is_weekday(cls, dt: datetime = None) -> bool:
        """
        判断是否为工作日（周一至周五）

        Args:
            dt: datetime 对象，默认为当前时间

        Returns:
            是否为工作日
        """
        if dt is None:
            dt = cls.get_china_time()

        # 0=周一, 6=周日
        return dt.weekday() < 5

    @classmethod
    def is_trading_hours(cls, dt: datetime = None) -> bool:
        """
        判断是否在交易时段

        Args:
            dt: datetime 对象，默认为当前时间

        Returns:
            是否在交易时段
        """
        if dt is None:
            dt = cls.get_china_time()

        # 首先检查是否为工作日
        if not cls.is_weekday(dt):
            return False

        current_time = dt.time()

        # 检查是否在上午交易时段
        if cls.MORNING_START <= current_time <= cls.MORNING_END:
            return True

        # 检查是否在下午交易时段
        if cls.AFTERNOON_START <= current_time <= cls.AFTERNOON_END:
            return True

        return False

    @classmethod
    def get_trading_status(cls, dt: datetime = None) -> Tuple[bool, str]:
        """
        获取交易状态

        Args:
            dt: datetime 对象，默认为当前时间

        Returns:
            (是否在交易时段, 状态描述)
        """
        if dt is None:
            dt = cls.get_china_time()

        if not cls.is_weekday(dt):
            weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][dt.weekday()]
            return False, f"非交易日 ({weekday_name})"

        current_time = dt.time()

        # 上午交易时段
        if cls.MORNING_START <= current_time <= cls.MORNING_END:
            return True, "上午交易时段"

        # 下午交易时段
        if cls.AFTERNOON_START <= current_time <= cls.AFTERNOON_END:
            return True, "下午交易时段"

        # 盘前
        if current_time < cls.MORNING_START:
            return False, "盘前"

        # 午休
        if cls.MORNING_END < current_time < cls.AFTERNOON_START:
            return False, "午休时段"

        # 盘后
        if current_time > cls.AFTERNOON_END:
            return False, "盘后"

        return False, "非交易时段"

    @classmethod
    def format_time(cls, dt: datetime = None) -> str:
        """
        格式化时间为中文显示

        Args:
            dt: datetime 对象，默认为当前时间

        Returns:
            格式化的时间字符串
        """
        if dt is None:
            dt = cls.get_china_time()

        weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][dt.weekday()]
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {weekday_name}"

    @classmethod
    def should_notify(cls, dt: datetime = None) -> bool:
        """
        判断是否应该发送通知（仅在交易时段）

        Args:
            dt: datetime 对象，默认为当前时间

        Returns:
            是否应该发送通知
        """
        return cls.is_trading_hours(dt)

    @classmethod
    def get_next_trading_time(cls, dt: datetime = None) -> datetime:
        """
        获取下一个交易时段的开始时间

        Args:
            dt: datetime 对象，默认为当前时间

        Returns:
            下一个交易时段的开始时间
        """
        if dt is None:
            dt = cls.get_china_time()

        current_time = dt.time()

        # 如果是工作日
        if cls.is_weekday(dt):
            # 如果在盘前，返回上午开盘时间
            if current_time < cls.MORNING_START:
                return dt.replace(
                    hour=cls.MORNING_START.hour,
                    minute=cls.MORNING_START.minute,
                    second=0,
                    microsecond=0
                )

            # 如果在午休，返回下午开盘时间
            if cls.MORNING_END < current_time < cls.AFTERNOON_START:
                return dt.replace(
                    hour=cls.AFTERNOON_START.hour,
                    minute=cls.AFTERNOON_START.minute,
                    second=0,
                    microsecond=0
                )

        # 其他情况，返回下一个工作日的上午开盘时间
        from datetime import timedelta
        next_day = dt + timedelta(days=1)

        while not cls.is_weekday(next_day):
            next_day += timedelta(days=1)

        return next_day.replace(
            hour=cls.MORNING_START.hour,
            minute=cls.MORNING_START.minute,
            second=0,
            microsecond=0
        )


# 便捷函数
def is_trading_hours() -> bool:
    """判断当前是否在交易时段"""
    return TimeUtils.is_trading_hours()


def should_notify() -> bool:
    """判断当前是否应该发送通知"""
    return TimeUtils.should_notify()


def get_trading_status() -> Tuple[bool, str]:
    """获取当前交易状态"""
    return TimeUtils.get_trading_status()
