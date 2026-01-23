"""
财联社爬虫（升级版 - 支持 JavaScript 渲染）
使用 Playwright 浏览器自动化
"""
from typing import List, Dict, Any
from datetime import datetime
from .browser_base import BrowserScraper


class CLSScraperV2(BrowserScraper):
    """财联社爬虫 v2 - 使用 Playwright"""

    def __init__(self):
        super().__init__(name='财联社')
        self.base_url = 'https://www.cls.cn/telegraph'

    def scrape(self) -> List[Dict[str, Any]]:
        """
        爬取财联社快讯

        Returns:
            新闻列表
        """
        print(f"[{self.name}] 开始爬取...")
        news_list = []

        try:
            # 使用 Playwright 获取页面内容
            # 等待快讯列表加载
            html_content = self.get_page_content(
                self.base_url,
                wait_selector='.item, .telegraph-item, .news-item',
                wait_time=5000
            )

            if not html_content:
                print(f"[{self.name}] 获取页面内容失败")
                return news_list

            # 解析 HTML
            soup = self.parse_html(html_content)
            if not soup:
                return news_list

            # 查找新闻项目 - 尝试多种选择器
            selectors = [
                ('div', {'class': 'item'}),
                ('div', {'class': 'telegraph-item'}),
                ('div', {'class': 'news-item'}),
                ('article', {}),
                ('li', {}),
            ]

            news_items = []
            for tag, attrs in selectors:
                if attrs:
                    news_items = soup.find_all(tag, attrs)
                else:
                    news_items = soup.find_all(tag)
                if news_items:
                    print(f"[{self.name}] 使用选择器 {tag} {attrs} 找到 {len(news_items)} 条新闻")
                    break

            if not news_items:
                print(f"[{self.name}] 警告: 未找到任何新闻项目")

            for item in news_items[:50]:
                try:
                    # 提取标题
                    title_elem = (
                        item.find('h3') or
                        item.find('h2') or
                        item.find('a', class_='title') or
                        item.find('a')
                    )
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    if not title or len(title) < 3:
                        continue

                    # 提取链接
                    link_elem = item.find('a', href=True)
                    url = link_elem['href'] if link_elem else ''
                    if url and not url.startswith('http'):
                        url = 'https://www.cls.cn' + url

                    # 提取内容
                    content_elem = (
                        item.find('p') or
                        item.find('span', class_='summary') or
                        item.find('div', class_='content')
                    )
                    content = content_elem.get_text(strip=True) if content_elem else title

                    # 提取时间
                    time_elem = (
                        item.find('span', class_='time') or
                        item.find('span', class_='date') or
                        item.find('span', class_='publish-time')
                    )
                    time_str = time_elem.get_text(strip=True) if time_elem else ''

                    # 解析时间
                    publish_time = self._parse_time(time_str)

                    # 标准化数据
                    news_item = self.normalize_news_item(
                        title=title,
                        content=content,
                        url=url,
                        publish_time=publish_time,
                        extra={'raw_time': time_str}
                    )

                    news_list.append(news_item)

                except Exception as e:
                    print(f"[{self.name}] 解析新闻项目失败: {e}")
                    continue

            print(f"[{self.name}] 成功爬取 {len(news_list)} 条新闻")

        except Exception as e:
            import traceback
            print(f"[{self.name}] 爬取失败: {e}")
            print(f"[{self.name}] 详细错误: {traceback.format_exc()}")

        return news_list

    def _parse_time(self, time_str: str) -> datetime:
        """解析时间字符串"""
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
                if dt.year == 1900:
                    now = datetime.now()
                    dt = dt.replace(year=now.year, month=now.month, day=now.day)
                return dt
            except ValueError:
                continue

        # 处理相对时间
        if '今天' in time_str or '今' in time_str:
            time_part = time_str.replace('今天', '').replace('今', '').strip()
            try:
                dt = datetime.strptime(time_part, '%H:%M')
                now = datetime.now()
                return dt.replace(year=now.year, month=now.month, day=now.day)
            except ValueError:
                pass

        return datetime.now()
