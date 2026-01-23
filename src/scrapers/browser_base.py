"""
Playwright 爬虫基类
支持 JavaScript 动态渲染的网站
"""
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[警告] Playwright 未安装，请运行: pip install playwright && playwright install chromium")


class BrowserScraper(ABC):
    """浏览器爬虫基类 - 支持 JavaScript 渲染"""

    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    ]

    def __init__(self, name: str, timeout: int = 30):
        """
        初始化浏览器爬虫

        Args:
            name: 爬虫名称
            timeout: 超时时间（秒）
        """
        self.name = name
        self.timeout = timeout * 1000  # Playwright 使用毫秒
        self.user_agent = random.choice(self.USER_AGENTS)

    def get_page_content(self, url: str, wait_selector: Optional[str] = None, wait_time: int = 5000) -> Optional[str]:
        """
        使用 Playwright 获取页面内容

        Args:
            url: 目标 URL
            wait_selector: CSS 选择器，等待该元素加载
            wait_time: 等待时间（毫秒）

        Returns:
            页面 HTML 内容
        """
        if not PLAYWRIGHT_AVAILABLE:
            print(f"[{self.name}] Playwright 未安装")
            return None

        try:
            with sync_playwright() as p:
                # 启动浏览器
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()

                print(f"[{self.name}] 正在加载页面: {url}")

                # 访问页面
                page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')

                # 如果指定了选择器，等待该元素加载
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=wait_time)
                        print(f"[{self.name}] 等待元素加载成功: {wait_selector}")
                    except Exception as e:
                        print(f"[{self.name}] 等待元素超时: {wait_selector} - {e}")

                # 等待额外时间，确保 JavaScript 执行完成
                page.wait_for_timeout(1000)

                # 获取页面内容
                content = page.content()

                # 关闭浏览器
                context.close()
                browser.close()

                print(f"[{self.name}] 页面加载成功，内容长度: {len(content)}")

                return content

        except Exception as e:
            print(f"[{self.name}] 浏览器加载失败: {e}")
            import traceback
            print(traceback.format_exc())
            return None

    def parse_html(self, html_content: str, parser: str = 'lxml') -> Optional[BeautifulSoup]:
        """
        解析 HTML 内容

        Args:
            html_content: HTML 内容
            parser: BeautifulSoup 解析器

        Returns:
            BeautifulSoup 对象
        """
        try:
            return BeautifulSoup(html_content, parser)
        except Exception as e:
            print(f"[{self.name}] HTML 解析失败: {e}")
            return None

    def normalize_news_item(
        self,
        title: str,
        content: str,
        url: str,
        publish_time: datetime,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        标准化新闻数据格式

        Args:
            title: 标题
            content: 内容
            url: 链接
            publish_time: 发布时间
            extra: 额外信息

        Returns:
            标准化的新闻数据
        """
        # 生成唯一 ID
        news_id = f"{self.name}_{publish_time.strftime('%Y%m%d%H%M%S')}_{hash(title) % 100000}"

        return {
            'id': news_id,
            'title': title.strip(),
            'content': content.strip(),
            'url': url,
            'publish_time': publish_time.isoformat(),
            'source': self.name,
            'scraped_at': datetime.now().isoformat(),
            'extra': extra or {}
        }

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        执行爬取任务（子类必须实现）

        Returns:
            标准化的新闻数据列表
        """
        pass

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
