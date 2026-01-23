"""
雪球爬虫
爬取雪球热门话题和快讯
"""
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from .base import BaseScraper


class XueqiuScraper(BaseScraper):
    """雪球爬虫"""

    def __init__(self):
        super().__init__(name='雪球', max_retries=3, timeout=10)
        self.base_url = 'https://xueqiu.com/hq'

    def scrape(self) -> List[Dict[str, Any]]:
        """
        爬取雪球热门话题

        Returns:
            新闻列表
        """
        print(f"[{self.name}] 开始爬取...")
        news_list = []

        try:
            # 设置额外的请求头，模拟浏览器
            headers = {
                'Referer': 'https://xueqiu.com/',
                'X-Requested-With': 'XMLHttpRequest',
            }

            # 发送请求
            response = self.make_request(self.base_url, headers=headers)
            if not response:
                print(f"[{self.name}] 请求失败")
                return news_list

            # 解析 HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # 查找新闻项目
            # 雪球的热门话题通常在特定的 div 中
            news_items = soup.find_all('div', class_='item')

            if not news_items:
                # 尝试其他选择器
                news_items = soup.find_all('li', class_='list-item')

            print(f"[{self.name}] 找到 {len(news_items)} 条新闻")

            for item in news_items[:30]:  # 限制最多 30 条
                try:
                    # 提取标题
                    title_elem = item.find('h3') or item.find('a', class_='title')
                    if not title_elem:
                        title_elem = item.find('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # 提取链接
                    link_elem = item.find('a', href=True)
                    url = link_elem['href'] if link_elem else ''
                    if url and not url.startswith('http'):
                        url = 'https://xueqiu.com' + url

                    # 提取内容/摘要
                    content_elem = item.find('p', class_='summary') or item.find('p')
                    content = content_elem.get_text(strip=True) if content_elem else title

                    # 提取时间
                    time_elem = item.find('span', class_='time') or item.find('span', class_='date')
                    time_str = time_elem.get_text(strip=True) if time_elem else ''

                    # 提取热度/点赞数（可选）
                    likes_elem = item.find('span', class_='likes')
                    likes = likes_elem.get_text(strip=True) if likes_elem else '0'

                    # 解析时间
                    publish_time = self._parse_time(time_str)

                    # 标准化数据
                    news_item = self.normalize_news_item(
                        title=title,
                        content=content,
                        url=url,
                        publish_time=publish_time,
                        extra={
                            'raw_time': time_str,
                            'likes': likes
                        }
                    )

                    news_list.append(news_item)

                except Exception as e:
                    print(f"[{self.name}] 解析新闻项目失败: {e}")
                    continue

            print(f"[{self.name}] 成功爬取 {len(news_list)} 条新闻")

        except Exception as e:
            print(f"[{self.name}] 爬取失败: {e}")

        return news_list

    def _parse_time(self, time_str: str) -> datetime:
        """
        解析时间字符串

        Args:
            time_str: 时间字符串，如 "10:30", "今天 10:30", "2026-01-23 10:30"

        Returns:
            datetime 对象
        """
        if not time_str:
            return datetime.now()

        time_str = time_str.strip()

        # 尝试多种时间格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%m-%d %H:%M:%S',
            '%m-%d %H:%M',
            '%H:%M:%S',
            '%H:%M',
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                # 如果没有年份，使用当前年份
                if dt.year == 1900:
                    now = datetime.now()
                    dt = dt.replace(year=now.year, month=now.month, day=now.day)
                return dt
            except ValueError:
                continue

        # 处理相对时间 "今天 10:30"
        if '今天' in time_str:
            time_part = time_str.replace('今天', '').strip()
            try:
                dt = datetime.strptime(time_part, '%H:%M')
                now = datetime.now()
                return dt.replace(year=now.year, month=now.month, day=now.day)
            except ValueError:
                pass

        # 如果都失败，返回当前时间
        return datetime.now()
