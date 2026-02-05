"""
新闻摘要生成器
生成一句话概述、关键标签、热度分数等
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re
import pytz
from .news_summary import NewsSummary


class SummaryGenerator:
    """新闻摘要生成器"""

    # 关键词到标签的映射
    KEYWORD_TO_TAGS = {
        '龙虎榜': ['龙虎榜', '机构', '游资'],
        '个股公告': ['公告', '业绩', '分红'],
        '大宗商品': ['商品', '期货', '原油'],
        '央行': ['央行', '货币政策', '降准'],
        '芯片': ['芯片', '半导体', '科技'],
        '新能源': ['新能源', '电动车', '光伏'],
        '医药': ['医药', '生物', '疫苗'],
        '房地产': ['房地产', '地产', '楼市'],
    }

    def __init__(self):
        """初始化生成器"""
        self.china_tz = pytz.timezone('Asia/Shanghai')

    def generate_snippet(self, news_item: Dict[str, Any], max_length: int = 150) -> str:
        """
        生成一句话概述

        Args:
            news_item: 新闻项目
            max_length: 最大长度

        Returns:
            概述文本
        """
        title = news_item.get('title', '')
        content = news_item.get('content', '')

        # 如果标题足够长，直接使用标题
        if len(title) > 50:
            return title[:max_length]

        # 否则从内容中提取关键信息
        if content:
            # 移除特殊字符和多余空格
            content = re.sub(r'\s+', ' ', content).strip()
            # 取前 max_length 个字符
            snippet = content[:max_length]
            # 如果被截断，添加省略号
            if len(content) > max_length:
                snippet = snippet.rsplit(' ', 1)[0] + '...'
            return snippet

        return title

    def extract_tags(self, news_item: Dict[str, Any]) -> List[str]:
        """
        提取关键标签

        Args:
            news_item: 新闻项目

        Returns:
            标签列表
        """
        tags = set()
        title = news_item.get('title', '').lower()
        content = news_item.get('content', '').lower()
        text = title + ' ' + content

        # 基于关键词提取标签
        for keyword, tag_list in self.KEYWORD_TO_TAGS.items():
            if keyword.lower() in text:
                tags.update(tag_list)

        # 添加分类作为标签
        category = news_item.get('category', '')
        if category:
            tags.add(category)

        return list(tags)[:5]  # 最多5个标签

    def calculate_score(self, news_item: Dict[str, Any], frequency: int = 1,
                       recency_minutes: int = 0) -> float:
        """
        计算热度分数

        Args:
            news_item: 新闻项目
            frequency: 相似新闻出现频次
            recency_minutes: 距离现在的分钟数

        Returns:
            热度分数（0-100）
        """
        # 频次权重（0.4）
        frequency_weight = min(frequency / 10.0, 1.0) * 40

        # 时效性权重（0.3）
        # 越新越高，24小时内为满分
        recency_weight = max(0, (1440 - recency_minutes) / 1440) * 30

        # 分类权重（0.2）
        category = news_item.get('category', '')
        category_weights = {
            '龙虎榜': 20,
            '个股公告': 18,
            '央行货币政策': 16,
            '监管政策': 15,
            '大宗商品': 12,
            '行业动态': 10,
            '商务部消息': 10,
            '国际市场': 8,
            '其他重要': 5,
        }
        category_weight = category_weights.get(category, 5)

        # 来源权重（0.1）
        source = news_item.get('source', '')
        source_weight = 10 if source == '财联社' else 5

        total_score = frequency_weight + recency_weight + category_weight + source_weight
        return min(total_score, 100.0)

    def calculate_recency_minutes(self, publish_time_str: str) -> int:
        """
        计算距离现在的分钟数

        Args:
            publish_time_str: 发布时间（ISO格式）

        Returns:
            分钟数
        """
        try:
            publish_time = datetime.fromisoformat(publish_time_str)
            if publish_time.tzinfo is None:
                publish_time = self.china_tz.localize(publish_time)
            now = datetime.now(self.china_tz)
            delta = now - publish_time
            return int(delta.total_seconds() / 60)
        except (ValueError, TypeError):
            return 0

    def generate_reason(self, news_item: Dict[str, Any], score: float) -> str:
        """
        生成上榜理由

        Args:
            news_item: 新闻项目
            score: 热度分数

        Returns:
            上榜理由
        """
        category = news_item.get('category', '')
        matched_keyword = news_item.get('matched_keyword', '')

        if score >= 80:
            return f"热度高 | {category}"
        elif score >= 60:
            return f"关键词：{matched_keyword}" if matched_keyword else category
        else:
            return category

    def generate_summary(self, news_item: Dict[str, Any], frequency: int = 1) -> NewsSummary:
        """
        生成完整的新闻摘要

        Args:
            news_item: 新闻项目
            frequency: 相似新闻出现频次

        Returns:
            NewsSummary 对象
        """
        # 计算时效性
        recency_minutes = self.calculate_recency_minutes(news_item.get('publish_time', ''))

        # 生成各个字段
        snippet = self.generate_snippet(news_item)
        tags = self.extract_tags(news_item)
        score = self.calculate_score(news_item, frequency, recency_minutes)
        reason = self.generate_reason(news_item, score)

        # 创建摘要对象
        return NewsSummary.from_news_item(
            news_item,
            snippet=snippet,
            score=score,
            tags=tags,
            reason=reason,
        )

    def generate_summaries(self, news_list: List[Dict[str, Any]]) -> List[NewsSummary]:
        """
        批量生成新闻摘要

        Args:
            news_list: 新闻列表

        Returns:
            摘要列表
        """
        summaries = []
        for news_item in news_list:
            summary = self.generate_summary(news_item)
            summaries.append(summary)

        # 按热度分数排序
        summaries.sort(key=lambda x: x.score, reverse=True)

        return summaries
