"""
雪球爬虫（改进版）
爬取雪球热门话题和讨论
"""
from typing import List, Dict, Any
from datetime import datetime
import json
from .browser_base import BrowserScraper


class XueqiuScraperImproved(BrowserScraper):
    """雪球爬虫 - 改进版，爬取热门话题"""

    def __init__(self):
        super().__init__(name='雪球')
        self.base_url = 'https://xueqiu.com/'

    def scrape(self) -> List[Dict[str, Any]]:
        """
        爬取雪球热门话题

        Returns:
            新闻列表
        """
        print(f"[{self.name}] 开始爬取...")
        news_list = []

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()

                print(f"[{self.name}] 正在加载页面: {self.base_url}")
                page.goto(self.base_url, wait_until='domcontentloaded', timeout=self.timeout)

                # 等待页面加载
                page.wait_for_timeout(3000)

                # 方法1：尝试从 API 响应中获取数据
                api_data = self._extract_from_network(page)
                if api_data:
                    news_list.extend(api_data)

                # 方法2：从 DOM 中提取热门话题
                if not news_list or len(news_list) < 5:
                    dom_data = self._extract_from_dom(page)
                    if dom_data:
                        news_list.extend(dom_data)

                context.close()
                browser.close()

            print(f"[{self.name}] 成功爬取 {len(news_list)} 条新闻")

        except Exception as e:
            import traceback
            print(f"[{self.name}] 爬取失败: {e}")
            print(f"[{self.name}] 详细错误: {traceback.format_exc()}")

        return news_list

    def _extract_from_network(self, page) -> List[Dict[str, Any]]:
        """从网络请求中提取数据"""
        news_list = []

        try:
            # 监听 API 响应
            responses = []

            def handle_response(response):
                if 'api' in response.url and response.status == 200:
                    try:
                        data = response.json()
                        responses.append(data)
                    except:
                        pass

            page.on('response', handle_response)

            # 等待一些 API 调用完成
            page.wait_for_timeout(2000)

            # 从响应中提取新闻
            for resp in responses:
                if isinstance(resp, dict) and 'data' in resp:
                    data = resp['data']
                    if isinstance(data, dict):
                        # 查找 items 或 list
                        items = data.get('items', []) or data.get('list', [])
                        if items:
                            for item in items[:20]:
                                try:
                                    title = item.get('name', '') or item.get('title', '')
                                    if title and len(title) > 3:
                                        symbol = item.get('symbol', '')
                                        url = f'https://xueqiu.com/S/{symbol}' if symbol else ''

                                        news_item = self.normalize_news_item(
                                            title=title,
                                            content=title,
                                            url=url,
                                            publish_time=datetime.now(),
                                            extra={'symbol': symbol}
                                        )
                                        news_list.append(news_item)
                                except:
                                    pass

        except Exception as e:
            print(f"[{self.name}] 网络数据提取失败: {e}")

        return news_list

    def _extract_from_dom(self, page) -> List[Dict[str, Any]]:
        """从 DOM 中提取热门话题"""
        news_list = []

        try:
            # 查找所有可能包含新闻的容器
            # 雪球的热门话题通常在特定的 div 中
            selectors = [
                'div[class*="feed"]',
                'div[class*="post"]',
                'div[class*="topic"]',
                'article',
                'div[class*="item"]'
            ]

            for selector in selectors:
                try:
                    items = page.query_selector_all(selector)
                    if items and len(items) > 3:
                        print(f"[{self.name}] 使用选择器 {selector} 找到 {len(items)} 个元素")

                        for item in items[:20]:
                            try:
                                # 提取标题
                                title_elem = item.query_selector('h3, h2, a, span[class*="title"]')
                                if not title_elem:
                                    continue

                                title = title_elem.inner_text().strip()
                                if not title or len(title) < 3 or len(title) > 200:
                                    continue

                                # 提取链接
                                link_elem = item.query_selector('a[href]')
                                url = link_elem.get_attribute('href') if link_elem else ''
                                if url and not url.startswith('http'):
                                    url = 'https://xueqiu.com' + url

                                # 提取内容/摘要
                                content_elem = item.query_selector('p, span[class*="summary"], div[class*="content"]')
                                content = content_elem.inner_text().strip() if content_elem else title

                                # 提取时间
                                time_elem = item.query_selector('span[class*="time"], span[class*="date"]')
                                time_str = time_elem.inner_text().strip() if time_elem else ''

                                news_item = self.normalize_news_item(
                                    title=title,
                                    content=content,
                                    url=url,
                                    publish_time=datetime.now(),
                                    extra={'raw_time': time_str}
                                )

                                news_list.append(news_item)

                            except Exception as e:
                                print(f"[{self.name}] 解析 DOM 项目失败: {e}")
                                continue

                        if news_list:
                            break

                except Exception as e:
                    print(f"[{self.name}] 选择器 {selector} 失败: {e}")
                    continue

        except Exception as e:
            print(f"[{self.name}] DOM 提取失败: {e}")

        return news_list
