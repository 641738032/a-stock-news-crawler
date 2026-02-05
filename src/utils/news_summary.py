"""
新闻摘要数据结构
用于结构化表示新闻摘要信息
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class NewsSummary:
    """新闻摘要数据结构"""

    title: str                          # 标题
    snippet: str                        # 一句话概述（100-150字）
    url: Optional[str] = None           # 原文链接
    source: str = "财联社"              # 来源
    publish_time: str = ""              # 发布时间（ISO格式）
    category: str = ""                  # 分类
    matched_keyword: str = ""           # 匹配的关键词
    score: float = 0.0                  # 热度/权重分数（0-100）
    tags: List[str] = field(default_factory=list)  # 关键标签
    reason: Optional[str] = None        # 为什么重要/上榜理由

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'title': self.title,
            'snippet': self.snippet,
            'url': self.url,
            'source': self.source,
            'publish_time': self.publish_time,
            'category': self.category,
            'matched_keyword': self.matched_keyword,
            'score': self.score,
            'tags': self.tags,
            'reason': self.reason,
        }

    @classmethod
    def from_news_item(cls, news_item: dict, snippet: str = "", score: float = 0.0,
                       tags: List[str] = None, reason: str = None) -> 'NewsSummary':
        """从新闻项创建摘要"""
        return cls(
            title=news_item.get('title', ''),
            snippet=snippet or news_item.get('title', ''),
            url=news_item.get('url'),
            source=news_item.get('source', '财联社'),
            publish_time=news_item.get('publish_time', ''),
            category=news_item.get('category', ''),
            matched_keyword=news_item.get('matched_keyword', ''),
            score=score,
            tags=tags or [],
            reason=reason,
        )

    def get_time_str(self, format_str: str = '%H:%M') -> str:
        """获取格式化的时间字符串"""
        try:
            dt = datetime.fromisoformat(self.publish_time)
            return dt.strftime(format_str)
        except (ValueError, TypeError):
            return ''

    def get_tags_str(self) -> str:
        """获取标签字符串（用 # 连接）"""
        if not self.tags:
            return ''
        return ' '.join(f'#{tag}' for tag in self.tags)
