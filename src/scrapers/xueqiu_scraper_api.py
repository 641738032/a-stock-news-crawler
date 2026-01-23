"""
雪球爬虫（API 版本）
直接调用 API 获取热门话题数据
"""
from typing import List, Dict, Any
from datetime import datetime
import requests
import json
from .base import BaseScraper


class XueqiuScraperAPI(BaseScraper):
    """雪球爬虫 - 使用 API"""

    def __init__(self):
        super().__init__(name='雪球')
        self.api_url = 'https://stock.xueqiu.com/v5/stock/hot_stock/list.json'

    def scrape(self) -> List[Dict[str, Any]]:
        """
        爬取雪球热门话题（通过 API）

        Returns:
            新闻列表
        """
        print(f"[{self.name}] 开始爬取...")
        news_list = []

        try:
            # API 参数
            params = {
                'page': '1',
                'size': '30',
                '_type': '10',
                'type': '10',
                'include': '1'
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

            items = data.get('data', {}).get('items', [])
            print(f"[{self.name}] 获取到 {len(items)} 条热门话题")

            for item in items:
                try:
                    # 提取字段
                    title = item.get('name', '').strip()
                    if not title or len(title) < 3:
                        continue

                    # 构建 URL
                    symbol = item.get('symbol', '')
                    url = f'https://xueqiu.com/S/{symbol}' if symbol else ''

                    # 提取内容
                    content = item.get('name', title)
                    if 'current_price' in item:
                        content += f" - 当前价格: {item['current_price']}"

                    # 时间戳转换
                    timestamp = item.get('timestamp', 0)
                    if timestamp:
                        publish_time = datetime.fromtimestamp(timestamp / 1000)  # 毫秒转秒
                    else:
                        publish_time = datetime.now()

                    # 标准化数据
                    news_item = self.normalize_news_item(
                        title=title,
                        content=content,
                        url=url,
                        publish_time=publish_time,
                        extra={
                            'symbol': symbol,
                            'current_price': item.get('current_price', 0),
                            'percent': item.get('percent', 0),
                            'volume': item.get('volume', 0)
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
