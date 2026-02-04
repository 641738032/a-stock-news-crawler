"""
数据管理模块
处理数据的读写、去重、增量检测等
"""
import json
import os
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta
import pytz


class DataManager:
    """数据管理器"""

    def __init__(self, data_dir: str = 'data'):
        """
        初始化数据管理器

        Args:
            data_dir: 数据目录
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def get_data_file(self, source: str) -> str:
        """获取数据文件路径"""
        return os.path.join(self.data_dir, f'{source}_news.json')

    def load_news(self, source: str) -> List[Dict[str, Any]]:
        """
        加载已保存的新闻数据

        Args:
            source: 数据源名称

        Returns:
            新闻列表
        """
        file_path = self.get_data_file(source)

        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[DataManager] 加载数据失败 ({source}): {e}")
            return []

    def save_news(self, source: str, news_list: List[Dict[str, Any]]) -> bool:
        """
        保存新闻数据

        Args:
            source: 数据源名称
            news_list: 新闻列表

        Returns:
            是否保存成功
        """
        file_path = self.get_data_file(source)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(news_list, f, ensure_ascii=False, indent=2)
            print(f"[DataManager] 保存数据成功 ({source}): {len(news_list)} 条新闻")
            return True
        except Exception as e:
            print(f"[DataManager] 保存数据失败 ({source}): {e}")
            return False

    def get_existing_ids(self, source: str) -> Set[str]:
        """
        获取已存在的新闻 ID 集合

        Args:
            source: 数据源名称

        Returns:
            ID 集合
        """
        news_list = self.load_news(source)
        return {news['id'] for news in news_list if 'id' in news}

    def detect_new_items(
        self,
        source: str,
        new_news_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        检测新增项目（增量检测）

        Args:
            source: 数据源名称
            new_news_list: 新爬取的新闻列表

        Returns:
            新增的新闻列表
        """
        existing_ids = self.get_existing_ids(source)
        new_items = [news for news in new_news_list if news['id'] not in existing_ids]

        print(f"[DataManager] {source}: 新增 {len(new_items)} 条新闻 (总共 {len(new_news_list)} 条)")

        return new_items

    def merge_news(
        self,
        source: str,
        new_news_list: List[Dict[str, Any]],
        max_items: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        合并新旧数据，保留最新的 max_items 条

        Args:
            source: 数据源名称
            new_news_list: 新爬取的新闻列表
            max_items: 最多保留的条数

        Returns:
            合并后的新闻列表
        """
        existing_news = self.load_news(source)
        existing_ids = {news['id'] for news in existing_news}

        # 过滤出新增的新闻
        new_items = [news for news in new_news_list if news['id'] not in existing_ids]

        # 合并数据
        merged = new_items + existing_news

        # 按发布时间排序（最新的在前）
        try:
            merged.sort(
                key=lambda x: x.get('publish_time', ''),
                reverse=True
            )
        except Exception as e:
            print(f"[DataManager] 排序失败: {e}")

        # 保留最新的 max_items 条
        merged = merged[:max_items]

        return merged

    def deduplicate_by_title(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按标题去重

        Args:
            news_list: 新闻列表

        Returns:
            去重后的新闻列表
        """
        seen_titles = set()
        deduplicated = []

        for news in news_list:
            title = news.get('title', '')
            if title not in seen_titles:
                seen_titles.add(title)
                deduplicated.append(news)

        if len(deduplicated) < len(news_list):
            print(f"[DataManager] 去重: {len(news_list)} -> {len(deduplicated)}")

        return deduplicated

    def archive_old_data(self, source: str, keep_days: int = 30) -> bool:
        """
        归档旧数据

        Args:
            source: 数据源名称
            keep_days: 保留天数

        Returns:
            是否归档成功
        """
        news_list = self.load_news(source)

        if not news_list:
            return True

        # 计算截断时间（使用北京时间）
        china_tz = pytz.timezone('Asia/Shanghai')
        cutoff_time = (datetime.now(china_tz) - timedelta(days=keep_days)).isoformat()

        # 分离新旧数据
        recent_news = []
        old_news = []

        for news in news_list:
            publish_time = news.get('publish_time', '')
            if publish_time >= cutoff_time:
                recent_news.append(news)
            else:
                old_news.append(news)

        # 保存最近的数据
        if recent_news:
            self.save_news(source, recent_news)

        # 保存旧数据到历史文件
        if old_news:
            china_tz = pytz.timezone('Asia/Shanghai')
            beijing_now = datetime.now(china_tz)
            archive_file = os.path.join(
                self.data_dir,
                'history',
                f'{source}_{beijing_now.strftime("%Y%m%d")}.json'
            )
            os.makedirs(os.path.dirname(archive_file), exist_ok=True)

            try:
                with open(archive_file, 'w', encoding='utf-8') as f:
                    json.dump(old_news, f, ensure_ascii=False, indent=2)
                print(f"[DataManager] 归档旧数据: {len(old_news)} 条 -> {archive_file}")
                return True
            except Exception as e:
                print(f"[DataManager] 归档失败: {e}")
                return False

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息

        Returns:
            统计信息
        """
        china_tz = pytz.timezone('Asia/Shanghai')
        stats = {
            'timestamp': datetime.now(china_tz).isoformat(),
            'sources': {}
        }

        for source in ['财联社', '雪球']:
            news_list = self.load_news(source)
            stats['sources'][source] = {
                'total_count': len(news_list),
                'latest_news': news_list[0] if news_list else None
            }

        return stats
