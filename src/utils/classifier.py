"""
新闻分类器模块
基于关键词匹配对财联社新闻进行分类
"""
from typing import List, Dict, Any, Tuple

# 每日分类定义
DAILY_CATEGORIES = {
    '龙虎榜': {
        'keywords': ['龙虎榜', '机构专用席位', '游资', '营业部', '买入席位', '卖出席位', '上榜'],
        'priority': 1,
        'color': '#ff6b6b'
    },
    '个股公告': {
        'keywords': ['公告', '业绩预告', '年报', '季报', '分红', '增持', '减持',
                    '股权激励', '重组', '并购', '停牌', '复牌', '归母净利润', '营业收入'],
        'priority': 2,
        'color': '#4ecdc4'
    },
    '大宗商品': {
        'keywords': ['白银', '黄金', '原油', '铜', '铝', '锌', '铁矿石', '煤炭',
                    '天然气', '大豆', '玉米', '小麦', '棉花', '橡胶', '期货', '现货'],
        'priority': 3,
        'color': '#f9ca24'
    },
    '商务部消息': {
        'keywords': ['商务部', '商务部新闻发言人', '商务部表示', '商务部发布'],
        'priority': 4,
        'color': '#6c5ce7'
    },
    '央行货币政策': {
        'keywords': ['央行', '中国人民银行', 'MLF', 'LPR', '降准', '降息', '逆回购',
                    '公开市场操作', '货币政策', '存款准备金'],
        'priority': 5,
        'color': '#a29bfe'
    },
    '监管政策': {
        'keywords': ['证监会', '银保监会', '发改委', '工信部', '财政部', '国资委',
                    '政策', '监管', '新规', '征求意见'],
        'priority': 6,
        'color': '#fd79a8'
    },
    '行业动态': {
        'keywords': ['芯片', '半导体', '新能源', '电动车', '光伏', '医药', '房地产',
                    '互联网', 'AI', '人工智能'],
        'priority': 7,
        'color': '#74b9ff'
    },
    '国际市场': {
        'keywords': ['美联储', '欧洲央行', '美股', '欧股', '日经', '恒指', '港股',
                    '美元', '欧元', '国际'],
        'priority': 8,
        'color': '#55efc4'
    },
    '其他重要': {
        'keywords': [],
        'priority': 99,
        'color': '#dfe6e9'
    }
}


def classify_news(news_item: Dict[str, Any]) -> Tuple[str, str]:
    """
    对单条新闻进行分类

    Args:
        news_item: 新闻项目字典，包含 title 和 content 字段

    Returns:
        (category_name, matched_keyword) 元组
    """
    title = news_item.get('title', '').lower()
    content = news_item.get('content', '').lower()
    text = title + ' ' + content

    matched_categories = []

    # 遍历所有分类（除了"其他重要"）
    for category, config in DAILY_CATEGORIES.items():
        if category == '其他重要':
            continue

        # 检查是否匹配该分类的任何关键词
        for keyword in config['keywords']:
            if keyword.lower() in text:
                matched_categories.append((category, config['priority'], keyword))
                break  # 每个分类只记录一次

    # 如果匹配到分类，按优先级排序，返回优先级最高的
    if matched_categories:
        matched_categories.sort(key=lambda x: x[1])
        return matched_categories[0][0], matched_categories[0][2]
    else:
        # 不匹配任何关键词，归入"其他重要"
        return '其他重要', ''


def classify_news_list(news_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    对新闻列表进行分类

    Args:
        news_list: 新闻列表

    Returns:
        分类字典 {category: [news1, news2, ...]}
    """
    classified = {category: [] for category in DAILY_CATEGORIES.keys()}

    for news in news_list:
        category, matched_keyword = classify_news(news)
        # 添加分类标记到新闻项
        news['category'] = category
        news['matched_keyword'] = matched_keyword
        classified[category].append(news)

    # 移除空分类
    classified = {k: v for k, v in classified.items() if v}

    return classified


def get_category_config(category: str) -> Dict[str, Any]:
    """
    获取分类配置

    Args:
        category: 分类名称

    Returns:
        分类配置字典
    """
    return DAILY_CATEGORIES.get(category, {})
