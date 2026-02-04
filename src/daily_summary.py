"""
A股每日新闻总结脚本
在北京时间 21:30 总结当天财联社的所有新闻
"""
import sys
import os
from datetime import datetime, time
from typing import List, Dict, Any

import pytz

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.data_manager import DataManager
from src.utils.logger import Logger
from src.utils.classifier import classify_news_list
from src.notifiers.daily_email import DailySummaryEmailNotifier


class DailySummaryApp:
    """每日新闻总结应用"""

    def __init__(self):
        """初始化应用"""
        self.data_manager = DataManager(data_dir='data')
        self.logger = Logger.get_logger()
        self.notifiers = self._init_notifiers()

    def _init_notifiers(self) -> Dict[str, DailySummaryEmailNotifier]:
        """
        初始化推送器

        Returns:
            推送器字典
        """
        notifiers = {}

        # 初始化邮件推送器
        email_config = self._get_email_config()
        if email_config:
            try:
                notifier = DailySummaryEmailNotifier(
                    smtp_host=email_config['smtp_host'],
                    smtp_port=email_config['smtp_port'],
                    sender=email_config['user'],
                    password=email_config['password'],
                    recipients=email_config['recipients'],
                    use_tls=email_config.get('use_tls', True)
                )
                notifiers['邮件'] = notifier
                self.logger.info("邮件推送器初始化成功")
            except Exception as e:
                self.logger.error(f"邮件推送器初始化失败: {e}")

        return notifiers

    def _get_email_config(self) -> Dict[str, Any]:
        """
        获取邮件配置

        Returns:
            邮件配置字典
        """
        try:
            smtp_port_str = os.getenv('EMAIL_SMTP_PORT', '587').strip()
            # 移除可能的冒号前缀
            if smtp_port_str.startswith(':'):
                smtp_port_str = smtp_port_str[1:]
            smtp_port = int(smtp_port_str)
        except (ValueError, AttributeError) as e:
            self.logger.error(f"邮件端口配置错误: {e}，使用默认端口 587")
            smtp_port = 587

        config = {
            'smtp_host': os.getenv('EMAIL_SMTP_HOST'),
            'smtp_port': smtp_port,
            'user': os.getenv('EMAIL_USER'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'recipients': os.getenv('EMAIL_RECIPIENTS', '').split(','),
            'use_tls': os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
        }

        # 检查必要的配置
        if not all([config['smtp_host'], config['user'], config['password'], config['recipients']]):
            self.logger.warning("邮件配置不完整，跳过邮件推送器初始化")
            self.logger.debug(f"配置检查: smtp_host={bool(config['smtp_host'])}, user={bool(config['user'])}, password={bool(config['password'])}, recipients={bool(config['recipients'])}")
            return None

        # 清理收件人列表
        config['recipients'] = [r.strip() for r in config['recipients'] if r.strip()]

        self.logger.info(f"邮件配置加载成功: host={config['smtp_host']}, port={config['smtp_port']}, user={config['user']}, recipients={config['recipients']}")

        return config

    def run(self):
        """运行每日总结"""
        self.logger.info("=" * 50)
        self.logger.info("开始生成每日新闻总结")
        self.logger.info("=" * 50)

        try:
            # 1. 加载财联社数据
            all_news = self.data_manager.load_news('财联社')
            self.logger.info(f"加载财联社数据: {len(all_news)} 条")

            if not all_news:
                self.logger.warning("财联社数据为空，跳过总结")
                return

            # 2. 确定当前时间段并过滤新闻
            china_tz = pytz.timezone('Asia/Shanghai')
            now_china = datetime.now(china_tz)
            current_hour = now_china.hour

            # 判断当前是早上 08:30 还是晚上 21:00
            # 早上 08:30 (允许 08:00-09:00 范围内执行)
            if 8 <= current_hour < 9:
                self.logger.info("当前时间段: 早上 08:30 (发送前一天 21:00 至今天 08:30 的新闻)")
                filtered_news = self._filter_news_morning(all_news, now_china)
                period_name = "前一天晚上21:00-今天早上08:30"
            # 晚上 21:00 (允许 20:30-21:30 范围内执行)
            elif 20 <= current_hour < 22:
                self.logger.info("当前时间段: 晚上 21:00 (发送今天 08:30 至晚上 21:00 的新闻)")
                filtered_news = self._filter_news_evening(all_news, now_china)
                period_name = "今天早上08:30-晚上21:00"
            else:
                self.logger.warning(f"当前时间 {now_china.strftime('%H:%M')} 不在预定的总结时间段内 (08:30 或 21:00)")
                return

            self.logger.info(f"过滤后新闻: {len(filtered_news)} 条 ({period_name})")

            if not filtered_news:
                self.logger.warning(f"时间段内没有新闻，跳过发送 ({period_name})")
                return

            # 3. 分类新闻
            classified_news = classify_news_list(filtered_news)
            self.logger.info(f"分类完成: {len(classified_news)} 个分类")

            # 4. 生成统计信息
            stats = self._generate_statistics(classified_news)
            self.logger.info(f"统计信息: {stats}")

            # 5. 发送邮件
            date_str = datetime.now(china_tz).strftime('%Y-%m-%d')
            self._send_daily_summary(classified_news, len(filtered_news), date_str, period_name)

            self.logger.info("=" * 50)
            self.logger.info("每日总结完成")
            self.logger.info("=" * 50)

        except Exception as e:
            self.logger.error(f"每日总结异常: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _filter_today_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤当天的新闻（北京时间）

        Args:
            news_list: 新闻列表

        Returns:
            当天的新闻列表
        """
        china_tz = pytz.timezone('Asia/Shanghai')
        now_china = datetime.now(china_tz)

        # 当天的开始和结束时间
        today_start = china_tz.localize(datetime.combine(now_china.date(), time.min))
        today_end = china_tz.localize(datetime.combine(now_china.date(), time.max))

        self.logger.info(f"过滤时间范围: {today_start.strftime('%Y-%m-%d %H:%M:%S')} ~ {today_end.strftime('%Y-%m-%d %H:%M:%S')}")

        today_news = []

        for news in news_list:
            try:
                publish_time_str = news.get('publish_time', '')
                if not publish_time_str:
                    continue

                # 解析发布时间
                if isinstance(publish_time_str, str):
                    publish_time = datetime.fromisoformat(publish_time_str)
                else:
                    publish_time = publish_time_str

                # 如果没有时区信息，假设是北京时间
                if publish_time.tzinfo is None:
                    publish_time = china_tz.localize(publish_time)

                # 检查是否在当天
                if today_start <= publish_time <= today_end:
                    today_news.append(news)

            except Exception as e:
                self.logger.warning(f"解析新闻时间失败: {e}")
                continue

        return today_news

    def _filter_news_morning(self, news_list: List[Dict[str, Any]], now_china: datetime) -> List[Dict[str, Any]]:
        """
        过滤早上 08:30 的新闻（前一天 21:00 至今天 08:30）

        Args:
            news_list: 新闻列表
            now_china: 当前北京时间

        Returns:
            过滤后的新闻列表
        """
        from datetime import timedelta
        china_tz = pytz.timezone('Asia/Shanghai')

        # 前一天 21:00
        yesterday = now_china.date() - timedelta(days=1)
        period_start = china_tz.localize(datetime.combine(yesterday, time(21, 0, 0)))

        # 今天 08:30
        period_end = china_tz.localize(datetime.combine(now_china.date(), time(8, 30, 0)))

        self.logger.info(f"早上过滤时间范围: {period_start.strftime('%Y-%m-%d %H:%M:%S')} ~ {period_end.strftime('%Y-%m-%d %H:%M:%S')}")

        filtered_news = []

        for news in news_list:
            try:
                publish_time_str = news.get('publish_time', '')
                if not publish_time_str:
                    continue

                # 解析发布时间
                if isinstance(publish_time_str, str):
                    publish_time = datetime.fromisoformat(publish_time_str)
                else:
                    publish_time = publish_time_str

                # 如果没有时区信息，假设是北京时间
                if publish_time.tzinfo is None:
                    publish_time = china_tz.localize(publish_time)

                # 检查是否在时间范围内
                if period_start <= publish_time <= period_end:
                    filtered_news.append(news)

            except Exception as e:
                self.logger.warning(f"解析新闻时间失败: {e}")
                continue

        return filtered_news

    def _filter_news_evening(self, news_list: List[Dict[str, Any]], now_china: datetime) -> List[Dict[str, Any]]:
        """
        过滤晚上 21:00 的新闻（今天 08:30 至晚上 21:00）

        Args:
            news_list: 新闻列表
            now_china: 当前北京时间

        Returns:
            过滤后的新闻列表
        """
        china_tz = pytz.timezone('Asia/Shanghai')

        # 今天 08:30
        period_start = china_tz.localize(datetime.combine(now_china.date(), time(8, 30, 0)))

        # 今天 21:00
        period_end = china_tz.localize(datetime.combine(now_china.date(), time(21, 0, 0)))

        self.logger.info(f"晚上过滤时间范围: {period_start.strftime('%Y-%m-%d %H:%M:%S')} ~ {period_end.strftime('%Y-%m-%d %H:%M:%S')}")

        filtered_news = []

        for news in news_list:
            try:
                publish_time_str = news.get('publish_time', '')
                if not publish_time_str:
                    continue

                # 解析发布时间
                if isinstance(publish_time_str, str):
                    publish_time = datetime.fromisoformat(publish_time_str)
                else:
                    publish_time = publish_time_str

                # 如果没有时区信息，假设是北京时间
                if publish_time.tzinfo is None:
                    publish_time = china_tz.localize(publish_time)

                # 检查是否在时间范围内
                if period_start <= publish_time <= period_end:
                    filtered_news.append(news)

            except Exception as e:
                self.logger.warning(f"解析新闻时间失败: {e}")
                continue

        return filtered_news

    def _generate_statistics(self, classified_news: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """
        生成统计信息

        Args:
            classified_news: 分类后的新闻字典

        Returns:
            统计信息字典
        """
        stats = {}
        for category, news_list in classified_news.items():
            stats[category] = len(news_list)
        return stats

    def _send_daily_summary(
        self,
        classified_news: Dict[str, List[Dict[str, Any]]],
        total_count: int,
        date_str: str,
        period_name: str = "当天"
    ):
        """
        发送每日总结

        Args:
            classified_news: 分类后的新闻字典
            total_count: 总新闻数
            date_str: 日期字符串
            period_name: 时间段名称
        """
        if not self.notifiers:
            self.logger.warning("没有可用的推送器")
            return

        for notifier_name, notifier in self.notifiers.items():
            try:
                success = notifier.send_daily_summary(classified_news, date_str, total_count, period_name)
                if not success:
                    self.logger.warning(f"{notifier_name} 推送失败")
            except Exception as e:
                self.logger.error(f"{notifier_name} 推送异常: {e}")


def main():
    """主函数"""
    try:
        app = DailySummaryApp()
        app.run()
    except Exception as e:
        logger = Logger.get_logger()
        logger.critical(f"应用异常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
