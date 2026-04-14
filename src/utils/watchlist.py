"""
持股仓工具模块
解析 WATCHLIST_STOCKS 环境变量，匹配相关新闻
"""
import os
from typing import List, Dict, Any


def parse_watchlist() -> List[List[str]]:
    """
    解析 WATCHLIST_STOCKS 环境变量

    格式：每个持仓条目用逗号分隔，条目内部用空格分隔（代码 名称 板块）
    示例：600519 贵州茅台 白酒,000858 五粮液 白酒,300750 宁德时代 新能源

    Returns:
        [[token, ...], ...] 每个条目的关键词列表
    """
    raw = os.getenv('WATCHLIST_STOCKS', '').strip()
    if not raw:
        return []
    entries = []
    for entry in raw.split(','):
        tokens = [t.strip() for t in entry.split() if t.strip()]
        if tokens:
            entries.append(tokens)
    return entries


def filter_watchlist_news(
    news_list: List[Dict[str, Any]],
    watchlist: List[List[str]]
) -> List[Dict[str, Any]]:
    """
    过滤与持股仓相关的新闻（title + content 中包含任意关键词）

    Args:
        news_list: 新闻列表
        watchlist: parse_watchlist() 返回的关键词列表

    Returns:
        匹配的新闻列表（去重，保持原顺序）
    """
    if not watchlist:
        return []

    all_tokens = {token for entry in watchlist for token in entry}
    seen_ids = set()
    result = []

    for news in news_list:
        news_id = news.get('id', id(news))
        if news_id in seen_ids:
            continue
        text = (news.get('title', '') + ' ' + news.get('content', ''))
        if any(token in text for token in all_tokens):
            seen_ids.add(news_id)
            result.append(news)

    return result
