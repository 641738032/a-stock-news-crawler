"""
新闻去重和聚类模块
基于相似度去重和聚类相似新闻
"""
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher
import re


class NewsDeduplicator:
    """新闻去重和聚类器"""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        初始化去重器

        Args:
            similarity_threshold: 相似度阈值（0-1），超过此阈值认为是相似新闻
        """
        self.similarity_threshold = similarity_threshold

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0-1）
        """
        # 标准化文本：转小写、移除特殊字符
        text1 = self._normalize_text(text1)
        text2 = self._normalize_text(text2)

        # 使用 SequenceMatcher 计算相似度
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()

    def _normalize_text(self, text: str) -> str:
        """
        标准化文本

        Args:
            text: 原始文本

        Returns:
            标准化后的文本
        """
        # 转小写
        text = text.lower()
        # 移除特殊字符，只保留中文、英文、数字和空格
        text = re.sub(r'[^\u4e00-\u9fa5a-z0-9\s]', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def deduplicate(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重新闻列表

        Args:
            news_list: 新闻列表

        Returns:
            去重后的新闻列表
        """
        if not news_list:
            return []

        deduplicated = []
        seen_indices = set()

        for i, news1 in enumerate(news_list):
            if i in seen_indices:
                continue

            deduplicated.append(news1)
            title1 = news1.get('title', '')

            # 与后续新闻比较
            for j in range(i + 1, len(news_list)):
                if j in seen_indices:
                    continue

                news2 = news_list[j]
                title2 = news2.get('title', '')

                # 计算相似度
                similarity = self.calculate_similarity(title1, title2)

                if similarity >= self.similarity_threshold:
                    seen_indices.add(j)

        return deduplicated

    def cluster_news(self, news_list: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        聚类相似新闻

        Args:
            news_list: 新闻列表

        Returns:
            聚类结果，每个簇是一个新闻列表
        """
        if not news_list:
            return []

        clusters = []
        assigned = set()

        for i, news1 in enumerate(news_list):
            if i in assigned:
                continue

            # 创建新簇
            cluster = [news1]
            assigned.add(i)
            title1 = news1.get('title', '')

            # 找出所有相似的新闻
            for j in range(i + 1, len(news_list)):
                if j in assigned:
                    continue

                news2 = news_list[j]
                title2 = news2.get('title', '')

                similarity = self.calculate_similarity(title1, title2)

                if similarity >= self.similarity_threshold:
                    cluster.append(news2)
                    assigned.add(j)

            clusters.append(cluster)

        return clusters

    def get_cluster_representative(self, cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        从簇中选择代表新闻

        选择标准：
        1. 优先选择最新的新闻
        2. 如果时间相同，选择内容最长的新闻

        Args:
            cluster: 新闻簇

        Returns:
            代表新闻
        """
        if not cluster:
            return {}

        # 按发布时间倒序排列
        sorted_cluster = sorted(
            cluster,
            key=lambda x: x.get('publish_time', ''),
            reverse=True
        )

        # 返回最新的新闻
        return sorted_cluster[0]

    def deduplicate_and_cluster(self, news_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[List[Dict[str, Any]]]]:
        """
        同时进行去重和聚类

        Args:
            news_list: 新闻列表

        Returns:
            (去重后的新闻列表, 聚类结果)
        """
        clusters = self.cluster_news(news_list)
        representatives = [self.get_cluster_representative(cluster) for cluster in clusters]
        return representatives, clusters
