"""
持股仓工具模块
解析 WATCHLIST_STOCKS 环境变量，匹配相关新闻
"""
import os
import re
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
    for entry in re.split(r'[,，;\n；]+', raw):
        entry = entry.strip()
        if not entry:
            continue

        tokens = [t.strip() for t in entry.split() if t.strip()]
        if tokens:
            entries.append(tokens)

    return entries


def flatten_watchlist_tokens(watchlist: List[List[str]]) -> List[str]:
    """
    将持股仓条目拍平成关键词列表（保持顺序，去重）。
    """
    seen = set()
    tokens = []
    for entry in watchlist:
        for token in entry:
            if token not in seen:
                seen.add(token)
                tokens.append(token)
    return tokens


def _normalize_text(text: str) -> str:
    """归一化文本：去空白 + 小写。"""
    return ''.join(text.split()).lower()


def _expand_token(token: str) -> List[str]:
    """
    扩展关键词，兼容常见写法差异：
    - 大小写差异（DeepSeek / deepseek）
    - 概念后缀（deepseek概念 -> deepseek）
    - ST 前缀（ST铖昌 -> 铖昌）
    """
    token = (token or '').strip()
    if not token:
        return []

    variants = {token}

    lowered = token.lower()
    variants.add(lowered)

    normalized = _normalize_text(token)
    variants.add(normalized)

    for suffix in ('概念', '板块', '产业链', '题材'):
        if token.endswith(suffix) and len(token) > len(suffix):
            base = token[:-len(suffix)].strip()
            if base:
                variants.add(base)
                variants.add(base.lower())
                variants.add(_normalize_text(base))

    no_st = re.sub(r'^\*?st', '', token, flags=re.IGNORECASE).strip()
    if no_st and no_st != token:
        variants.add(no_st)
        variants.add(no_st.lower())
        variants.add(_normalize_text(no_st))

    if token.isdigit():
        variants.add(token.zfill(6))

    return [v for v in variants if v and (len(v) >= 2 or v.isdigit())]


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

    raw_tokens = flatten_watchlist_tokens(watchlist)
    all_tokens = set()
    normalized_tokens = set()
    for token in raw_tokens:
        for variant in _expand_token(token):
            all_tokens.add(variant)
            normalized_tokens.add(_normalize_text(variant))

    seen_ids = set()
    result = []

    for news in news_list:
        news_id = news.get('id', id(news))
        if news_id in seen_ids:
            continue

        title = str(news.get('title', ''))
        content = str(news.get('content', ''))
        text = f"{title} {content}"
        lower_text = text.lower()
        normalized_text = _normalize_text(text)

        matched = any(token in text or token in lower_text for token in all_tokens)
        if not matched:
            matched = any(token and token in normalized_text for token in normalized_tokens)

        if matched:
            seen_ids.add(news_id)
            result.append(news)

    return result
