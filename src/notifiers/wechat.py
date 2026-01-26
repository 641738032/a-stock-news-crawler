"""
企业微信推送模块
通过企业微信群机器人发送消息
"""
import requests
from typing import List, Dict, Any
from .base import BaseNotifier


class WeChatNotifier(BaseNotifier):
    """企业微信推送器"""

    def __init__(self, webhook_url: str):
        """
        初始化企业微信推送器

        Args:
            webhook_url: 企业微信群机器人 webhook URL
        """
        super().__init__(name='企业微信')
        self.webhook_url = webhook_url

    def send(self, news_list: List[Dict[str, Any]], source: str = '') -> bool:
        """
        发送企业微信消息

        Args:
            news_list: 新闻列表
            source: 数据源名称

        Returns:
            是否发送成功
        """
        if not news_list:
            print(f"[{self.name}] 没有新闻需要推送")
            return True

        if not self.webhook_url:
            print(f"[{self.name}] webhook_url 未配置")
            return False

        try:
            # 构建消息
            message = self._build_message(news_list, source)

            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print(f"[{self.name}] 推送成功 ({source}): {len(news_list)} 条新闻")
                    return True
                else:
                    print(f"[{self.name}] 推送失败: {result.get('errmsg')}")
                    return False
            else:
                print(f"[{self.name}] 请求失败: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"[{self.name}] 推送异常: {e}")
            return False

    def _build_message(self, news_list: List[Dict[str, Any]], source: str = '') -> Dict[str, Any]:
        """
        构建企业微信消息

        Args:
            news_list: 新闻列表
            source: 数据源名称

        Returns:
            消息字典
        """
        # 构建新闻内容
        content_lines = []
        content_lines.append(f"📰 **A股新闻播报** ({source})")
        content_lines.append(f"⏰ 共 {len(news_list)} 条新闻\n")

        # 添加热点总结
        summary = self._generate_summary(news_list)
        if summary:
            content_lines.append("**🔥 热点总结**")
            content_lines.extend(summary)
            content_lines.append("")

        for i, news in enumerate(news_list[:10], 1):  # 最多显示 10 条
            title = news.get('title', '无标题')
            url = news.get('url', '')
            publish_time = news.get('publish_time', '')

            # 提取时间部分
            time_str = ''
            if publish_time:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(publish_time)
                    time_str = dt.strftime('%H:%M')
                except:
                    pass

            content_lines.append(f"**{i}. {title}**")
            if time_str:
                content_lines.append(f"时间: {time_str}")
            if url:
                content_lines.append(f"[查看详情]({url})")
            content_lines.append("")

        content = '\n'.join(content_lines)

        # 构建企业微信消息格式
        message = {
            'msgtype': 'markdown',
            'markdown': {
                'content': content
            }
        }

        return message

    def _generate_summary(self, news_list: List[Dict[str, Any]]) -> List[str]:
        """
        生成新闻热点总结

        Args:
            news_list: 新闻列表

        Returns:
            总结行列表
        """
        if not news_list:
            return []

        # 关键词和板块映射
        sector_keywords = {
            '芯片': ['芯片', '半导体', 'IC', '集成电路', '光刻', '制程'],
            '新能源': ['新能源', '电动车', 'EV', '电池', '光伏', '风电', '储能'],
            '医药': ['医药', '制药', '生物', '疫苗', '药物', '医疗'],
            '房地产': ['房地产', '地产', '房企', '楼市', '房价', '开发商'],
            '金融': ['银行', '保险', '证券', '基金', '金融', '理财'],
            '消费': ['消费', '零售', '电商', '餐饮', '服装', '家电'],
            '科技': ['科技', '互联网', '软件', '云计算', '大数据', 'AI', '人工智能'],
            '制造': ['制造', '工业', '机械', '汽车', '装备'],
            '资源': ['煤炭', '石油', '有色', '钢铁', '资源'],
        }

        # 统计各板块出现次数
        sector_count = {}
        sector_examples = {}

        for news in news_list:
            title = news.get('title', '').lower()
            content = news.get('content', '').lower()
            text = title + content

            for sector, keywords in sector_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        sector_count[sector] = sector_count.get(sector, 0) + 1
                        if sector not in sector_examples:
                            sector_examples[sector] = title[:30]
                        break

        # 获取前3个热点板块
        sorted_sectors = sorted(sector_count.items(), key=lambda x: x[1], reverse=True)[:3]

        summary_lines = []
        for idx, (sector, count) in enumerate(sorted_sectors, 1):
            example = sector_examples.get(sector, '')
            summary_lines.append(f"{idx}. **{sector}** ({count}条) - {example}...")

        return summary_lines
