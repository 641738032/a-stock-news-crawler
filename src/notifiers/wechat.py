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
