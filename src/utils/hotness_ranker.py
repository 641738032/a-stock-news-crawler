"""
热度排序模块
基于多个因素计算新闻热度分数并排序
"""
from typing import List, Dict, Any
from datetime import datetime
import pytz


class HotnessRanker:
    """热度排序器"""

    def __init__(self):
        """初始化排序器"""
        self.china_tz = pytz.timezone('Asia/Shanghai')

        # 分类权重
        self.category_weights = {
            '龙虎榜': 1.0,
            '个股公告': 0.9,
            '央行货币政策': 0.8,
            '监管政策': 0.8,
            '商务部消息': 0.7,
            '大宗商品': 0.6,
            '行业动态': 0.5,
            '国际市场': 0.4,
            '其他重要': 0.3,
        }

        # 来源权重
        self.source_weights = {
            '财联社': 1.0,
            '雪球': 0.8,
        }

    def calculate_frequency_score(self, frequency: int, max_frequency: int = 10) -> float:
        """
        计算频次分数

        Args:
            frequency: 相似新闻出现频次
            max_frequency: 最大频次（用于归一化）

        Returns:
            频次分数（0-1）
        """
        return min(frequency / max_frequency, 1.0)

    def calculate_recency_score(self, publish_time_str: str) -> float:
        """
        计算时效性分数

        Args:
            publish_time_str: 发布时间（ISO格式）

        Returns:
            时效性分数（0-1），越新越高
        """
        try:
            publish_time = datetime.fromisoformat(publish_time_str)
            if publish_time.tzinfo is None:
                publish_time = self.china_tz.localize(publish_time)

            now = datetime.now(self.china_tz)
            delta = now - publish_time
            minutes_ago = delta.total_seconds() / 60

            # 24小时内为满分，超过24小时线性递减
            if minutes_ago <= 1440:  # 24小时
                return 1.0 - (minutes_ago / 1440) * 0.5  # 最低0.5分
            else:
                return max(0, 0.5 - ((minutes_ago - 1440) / 1440) * 0.5)  # 最低0分

        except (ValueError, TypeError):
            return 0.5  # 默认分数

    def calculate_category_score(self, category: str) -> float:
        """
        计算分类权重分数

        Args:
            category: 分类名称

        Returns:
            分类权重分数（0-1）
        """
        return self.category_weights.get(category, 0.3)

    def calculate_source_score(self, source: str) -> float:
        """
        计算来源权重分数

        Args:
            source: 来源名称

        Returns:
            来源权重分数（0-1）
        """
        return self.source_weights.get(source, 0.5)

    def calculate_hotness_score(
        self,
        news_item: Dict[str, Any],
        frequency: int = 1,
        frequency_weight: float = 0.4,
        recency_weight: float = 0.3,
        category_weight: float = 0.2,
        source_weight: float = 0.1
    ) -> float:
        """
        计算综合热度分数

        公式：
        score = frequency_score * frequency_weight +
                recency_score * recency_weight +
                category_score * category_weight +
                source_score * source_weight

        Args:
            news_item: 新闻项目
            frequency: 相似新闻出现频次
            frequency_weight: 频次权重
            recency_weight: 时效性权重
            category_weight: 分类权重
            source_weight: 来源权重

        Returns:
            热度分数（0-100）
        """
        # 计算各个分数
        frequency_score = self.calculate_frequency_score(frequency)
        recency_score = self.calculate_recency_score(news_item.get('publish_time', ''))
        category_score = self.calculate_category_score(news_item.get('category', ''))
        source_score = self.calculate_source_score(news_item.get('source', ''))

        # 加权求和
        total_score = (
            frequency_score * frequency_weight +
            recency_score * recency_weight +
            category_score * category_weight +
            source_score * source_weight
        )

        # 转换为 0-100 分
        return total_score * 100

    def rank_news(
        self,
        news_list: List[Dict[str, Any]],
        frequency_map: Dict[str, int] = None,
        top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        对新闻列表进行热度排序

        Args:
            news_list: 新闻列表
            frequency_map: 频次映射 {news_id: frequency}
            top_n: 返回前N条（None表示返回全部）

        Returns:
            排序后的新闻列表
        """
        if not news_list:
            return []

        frequency_map = frequency_map or {}

        # 计算每条新闻的热度分数
        scored_news = []
        for news in news_list:
            news_id = news.get('id', '')
            frequency = frequency_map.get(news_id, 1)
            score = self.calculate_hotness_score(news, frequency)

            # 添加分数到新闻项
            news_with_score = news.copy()
            news_with_score['hotness_score'] = score

            scored_news.append(news_with_score)

        # 按热度分数排序
        ranked_news = sorted(scored_news, key=lambda x: x['hotness_score'], reverse=True)

        # 返回前N条
        if top_n:
            return ranked_news[:top_n]
        else:
            return ranked_news

    def get_top_news(
        self,
        news_list: List[Dict[str, Any]],
        top_n: int = 10,
        frequency_map: Dict[str, int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取热度最高的前N条新闻

        Args:
            news_list: 新闻列表
            top_n: 返回条数
            frequency_map: 频次映射

        Returns:
            热度最高的前N条新闻
        """
        return self.rank_news(news_list, frequency_map, top_n)
