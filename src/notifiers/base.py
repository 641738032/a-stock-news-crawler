"""
推送基类
定义推送接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseNotifier(ABC):
    """推送基类"""

    def __init__(self, name: str):
        """
        初始化推送器

        Args:
            name: 推送器名称
        """
        self.name = name

    @abstractmethod
    def send(self, news_list: List[Dict[str, Any]], source: str = '') -> bool:
        """
        发送推送消息

        Args:
            news_list: 新闻列表
            source: 数据源名称

        Returns:
            是否发送成功
        """
        pass

    def format_news_summary(self, news_list: List[Dict[str, Any]], max_items: int = 10) -> str:
        """
        格式化新闻摘要

        Args:
            news_list: 新闻列表
            max_items: 最多显示的条数

        Returns:
            格式化的摘要文本
        """
        if not news_list:
            return "暂无新闻"

        summary_lines = []

        for i, news in enumerate(news_list[:max_items], 1):
            title = news.get('title', '无标题')
            url = news.get('url', '')
            publish_time = news.get('publish_time', '')

            # 提取时间部分（HH:MM）
            time_str = ''
            if publish_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(publish_time)
                    time_str = dt.strftime('%H:%M')
                except:
                    pass

            summary_lines.append(f"{i}. [{time_str}] {title}")
            if url:
                summary_lines.append(f"   {url}")

        return '\n'.join(summary_lines)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
