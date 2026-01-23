"""
雪球爬虫（登录版本）
使用 Playwright 登录后爬取数据
"""
from typing import List, Dict, Any
from datetime import datetime
import json
from .browser_base import BrowserScraper


class XueqiuScraperLogin(BrowserScraper):
    """雪球爬虫 - 使用 Playwright 登录"""

    def __init__(self):
        super().__init__(name='雪球')
        self.base_url = 'https://xueqiu.com/hq'

    def scrape(self) -> List[Dict[str, Any]]:
        """
        爬取雪球热门话题（通过 Playwright 登录）

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

                # 提取页面中的 API 数据
                # 雪球使用 window.__INITIAL_STATE__ 存储数据
                try:
                    # 尝试从页面中提取 JSON 数据
                    script_content = page.evaluate("""
                        () => {
                            // 查找所有包含数据的 script 标签
                            const scripts = document.querySelectorAll('script');
                            for (let script of scripts) {
                                if (script.textContent.includes('__INITIAL_STATE__')) {
                                    return script.textContent;
                                }
                            }
                            return null;
                        }
                    """)

                    if script_content:
                        print(f"[{self.name}] 找到初始数据")
                        # 解析 JSON
                        try:
                            start = script_content.find('{')
                            end = script_content.rfind('}') + 1
                            if start != -1 and end > start:
                                json_str = script_content[start:end]
                                data = json.loads(json_str)
                                # 从数据中提取新闻
                                news_list = self._extract_news_from_data(data)
                        except Exception as e:
                            print(f"[{self.name}] 解析初始数据失败: {e}")

                except Exception as e:
                    print(f"[{self.name}] 提取页面数据失败: {e}")

                # 如果上面方法失败，尝试从 DOM 中提取
                if not news_list:
                    print(f"[{self.name}] 尝试从 DOM 中提取数据...")
                    news_list = self._extract_from_dom(page)

                context.close()
                browser.close()

            print(f"[{self.name}] 成功爬取 {len(news_list)} 条新闻")

        except Exception as e:
            import traceback
            print(f"[{self.name}] 爬取失败: {e}")
            print(f"[{self.name}] 详细错误: {traceback.format_exc()}")

        return news_list

    def _extract_news_from_data(self, data: Dict) -> List[Dict[str, Any]]:
        """从 JSON 数据中提取新闻"""
        news_list = []

        def find_items(obj, depth=0):
            if depth > 10:
                return
            if isinstance(obj, dict):
                # 查找包含新闻数据的字段
                if 'items' in obj and isinstance(obj['items'], list):
                    for item in obj['items'][:30]:
                        try:
                            title = item.get('name', '') or item.get('title', '')
                            if title and len(title) > 3:
                                symbol = item.get('symbol', '')
                                url = f'https://xueqiu.com/S/{symbol}' if symbol else ''
                                content = title
                                if 'current_price' in item:
                                    content += f" - {item['current_price']}"

                                news_item = self.normalize_news_item(
                                    title=title,
                                    content=content,
                                    url=url,
                                    publish_time=datetime.now(),
                                    extra={
                                        'symbol': symbol,
                                        'price': item.get('current_price', 0),
                                        'percent': item.get('percent', 0)
                                    }
                                )
                                news_list.append(news_item)
                        except Exception as e:
                            print(f"[{self.name}] 解析项目失败: {e}")
                            continue

                for v in obj.values():
                    find_items(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    find_items(item, depth + 1)

        find_items(data)
        return news_list

    def _extract_from_dom(self, page) -> List[Dict[str, Any]]:
        """从 DOM 中提取新闻"""
        news_list = []

        try:
            # 查找所有可能的新闻容器
            items = page.query_selector_all('div[class*="item"], li[class*="item"], article')

            for item in items[:30]:
                try:
                    # 提取标题
                    title_elem = item.query_selector('h3, h2, a')
                    if not title_elem:
                        continue

                    title = title_elem.inner_text().strip()
                    if not title or len(title) < 3:
                        continue

                    # 提取链接
                    link_elem = item.query_selector('a[href]')
                    url = link_elem.get_attribute('href') if link_elem else ''
                    if url and not url.startswith('http'):
                        url = 'https://xueqiu.com' + url

                    # 提取内容
                    content_elem = item.query_selector('p, span')
                    content = content_elem.inner_text() if content_elem else title

                    news_item = self.normalize_news_item(
                        title=title,
                        content=content,
                        url=url,
                        publish_time=datetime.now(),
                        extra={}
                    )

                    news_list.append(news_item)

                except Exception as e:
                    print(f"[{self.name}] 解析 DOM 项目失败: {e}")
                    continue

        except Exception as e:
            print(f"[{self.name}] DOM 提取失败: {e}")

        return news_list
