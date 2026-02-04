"""
爬虫基类
提供通用的请求方法、错误处理和数据标准化接口
"""
import time
import random
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz


class BaseScraper(ABC):
    """爬虫基类"""

    # User-Agent 列表，用于轮换
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]

    def __init__(self, name: str, max_retries: int = 3, timeout: int = 10):
        """
        初始化爬虫

        Args:
            name: 爬虫名称
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
        """
        self.name = name
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()

    def get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(self.USER_AGENTS)

    def make_request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Optional[requests.Response]:
        """
        发送 HTTP 请求，带重试机制

        Args:
            url: 请求 URL
            method: 请求方法 (GET/POST)
            headers: 请求头
            params: URL 参数
            data: 表单数据
            json: JSON 数据

        Returns:
            Response 对象，失败返回 None
        """
        # 设置默认 headers
        default_headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        if headers:
            default_headers.update(headers)

        # 重试机制
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=default_headers,
                    params=params,
                    data=data,
                    json=json,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                print(f"[{self.name}] 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    # 指数退避
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"[{self.name}] 等待 {wait_time:.2f} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"[{self.name}] 达到最大重试次数，请求失败")
                    return None

        return None

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        执行爬取任务（子类必须实现）

        Returns:
            标准化的新闻数据列表，每条新闻包含以下字段：
            - id: 唯一标识
            - title: 标题
            - content: 内容/摘要
            - url: 链接
            - publish_time: 发布时间 (ISO 8601 格式)
            - source: 来源
            - extra: 额外信息（可选）
        """
        pass

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
        # 生成唯一 ID (使用标题和时间的组合)
        news_id = f"{self.name}_{publish_time.strftime('%Y%m%d%H%M%S')}_{hash(title) % 100000}"

        china_tz = pytz.timezone('Asia/Shanghai')
        return {
            'id': news_id,
            'title': title.strip(),
            'content': content.strip(),
            'url': url,
            'publish_time': publish_time.isoformat(),
            'source': self.name,
            'scraped_at': datetime.now(china_tz).isoformat(),
            'extra': extra or {}
        }

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
