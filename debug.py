#!/usr/bin/env python3
"""
爬虫调试脚本
用于诊断爬虫问题和测试网站可访问性
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.cls_scraper_api import CLSScraperAPI
from src.scrapers.xueqiu_scraper_improved import XueqiuScraperImproved
from src.utils.time_utils import get_trading_status


def test_scrapers():
    """测试爬虫"""
    print("=" * 60)
    print("A股新闻爬虫 - 调试脚本")
    print("=" * 60)

    # 检查交易时段
    is_trading, status = get_trading_status()
    print(f"\n当前交易状态: {status}")
    print(f"是否在交易时段: {is_trading}")

    # 测试财联社爬虫
    print("\n" + "=" * 60)
    print("测试财联社爬虫")
    print("=" * 60)
    cls_scraper = CLSScraperAPI()
    cls_news = cls_scraper.scrape()
    print(f"\n爬取结果: {len(cls_news)} 条新闻")
    if cls_news:
        print("\n前 3 条新闻:")
        for i, news in enumerate(cls_news[:3], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   URL: {news['url']}")
            print(f"   时间: {news['publish_time']}")

    # 测试雪球爬虫
    print("\n" + "=" * 60)
    print("测试雪球爬虫")
    print("=" * 60)
    xueqiu_scraper = XueqiuScraperImproved()
    xueqiu_news = xueqiu_scraper.scrape()
    print(f"\n爬取结果: {len(xueqiu_news)} 条新闻")
    if xueqiu_news:
        print("\n前 3 条新闻:")
        for i, news in enumerate(xueqiu_news[:3], 1):
            print(f"\n{i}. {news['title']}")
            print(f"   URL: {news['url']}")
            print(f"   时间: {news['publish_time']}")

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_scrapers()
