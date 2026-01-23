"""
财联社爬虫（API 版本）
直接调用 API 获取数据，不依赖 HTML 解析
"""
from typing import List, Dict, Any
from datetime import datetime
import requests
import json
from .base import BaseScraper


class CLSScraperAPI(BaseScraper):
    """财联社爬虫 - 使用 API"""

    def __init__(self):
        super().__init__(name='财联社')
        self.api_url = 'https://www.cls.cn/nodeapi/updateTelegraphList'

    def scrape(self) -> List[Dict[str, Any]]:
        """
        爬取财联社快讯（通过 API）

        Returns:
            新闻列表
        """
        print(f"[{self.name}] 开始爬取...")
        news_list = []

        try:
            # API 参数
            params = {
                'app': 'CailianpressWeb',
                'hasFirstVipArticle': '0',
                'lastTime': '0',
                'os': 'web',
                'rn': '50',  # 获取 50 条
                'subscribedColumnIds': '',
                'sv': '8.4.6',
                'sign': 'b397ff36b4640016fe5b07a29fa2d521'
            }

            # 发送请求
            response = self.make_request(self.api_url, params=params)
            if not response:
                print(f"[{self.name}] 请求失败")
                return news_list

            print(f"[{self.name}] 响应状态码: {response.status_code}")

            # 解析 JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"[{self.name}] JSON 解析失败")
                return news_list

            # 检查响应结构
            if 'data' not in data:
                print(f"[{self.name}] 响应中没有 data 字段")
                print(f"[{self.name}] 响应键: {list(data.keys())}")
                return news_list

            telegraph_list = data.get('data', {}).get('roll_data', [])
            print(f"[{self.name}] 获取到 {len(telegraph_list)} 条快讯")

            for item in telegraph_list:
                try:
                    # 提取字段 - 财联社 API 返回的是 brief 和 content
                    title = item.get('brief', '').strip()
                    if not title or len(title) < 3:
                        continue

                    content = item.get('content', title).strip()
                    # 财联社 API 没有直接的 URL，构建链接
                    article_id = item.get('id', '')
                    url = f'https://www.cls.cn/telegraph/{article_id}' if article_id else ''

                    # 时间戳转换
                    timestamp = item.get('ctime', 0)
                    if timestamp:
                        publish_time = datetime.fromtimestamp(timestamp)
                    else:
                        publish_time = datetime.now()

                    # 标准化数据
                    news_item = self.normalize_news_item(
                        title=title,
                        content=content,
                        url=url,
                        publish_time=publish_time,
                        extra={
                            'raw_time': str(timestamp),
                            'source_id': item.get('id', '')
                        }
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
