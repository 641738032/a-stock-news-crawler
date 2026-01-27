"""
本地定时任务调度器
1. 每个整点执行爬取并推送
2. 早上 8:30 发送前一天晚上 9 点以后至今天早上 8:30 的新闻总结
3. 晚上 21:00 发送当天早上 8:30 至晚上 21:00 的新闻总结
"""
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

import schedule
import pytz

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.main import CrawlerApp
from src.utils.data_manager import DataManager
from src.utils.logger import Logger
from src.utils.classifier import classify_news_list
from src.notifiers.daily_email import DailySummaryEmailNotifier
from src.notifiers.wechat import WeChatNotifier


class SchedulerApp:
    """定时任务调度应用"""

    def __init__(self):
        """初始化调度应用"""
        self.logger = Logger.get_logger('scheduler')
        self.data_manager = DataManager(data_dir='data')
        self.crawler_app = CrawlerApp()
        self.notifiers = self.crawler_app.notifiers
        self.china_tz = pytz.timezone('Asia/Shanghai')

    def run(self):
        """启动调度器"""
        self.logger.info("=" * 60)
        self.logger.info("A股新闻定时调度器启动")
        self.logger.info("=" * 60)
        self.logger.info("任务计划:")
        self.logger.info("  - 每个整点: 爬取新闻并推送")
        self.logger.info("  - 早上 08:30: 发送前一天晚上 21:00 至今天 08:30 的总结")
        self.logger.info("  - 晚上 21:00: 发送今天 08:30 至晚上 21:00 的总结")
        self.logger.info("=" * 60)

        # 注册定时任务
        schedule.every().hour.at(":00").do(self._hourly_crawl)
        schedule.every().day.at("08:30").do(self._morning_summary)
        schedule.every().day.at("21:00").do(self._evening_summary)

        # 运行调度器
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("调度器已停止")
                break
            except Exception as e:
                self.logger.error(f"调度器异常: {e}")
                time.sleep(60)

    def _hourly_crawl(self):
        """每个整点执行爬取"""
        now = datetime.now(self.china_tz)
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"执行每小时爬取任务 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"{'=' * 60}")

        try:
            self.crawler_app.run()
        except Exception as e:
            self.logger.error(f"爬取任务异常: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _morning_summary(self):
        """早上 8:30 发送总结"""
        now = datetime.now(self.china_tz)
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"执行早上总结任务 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"{'=' * 60}")

        try:
            # 计算时间范围: 前一天晚上 21:00 至今天 08:30
            today = now.date()
            yesterday = today - timedelta(days=1)

            start_time = self.china_tz.localize(datetime.combine(yesterday, datetime.min.time().replace(hour=21, minute=0)))
            end_time = now

            self.logger.info(f"总结时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # 加载新闻
            all_news = self.data_manager.load_news('财联社')
            filtered_news = self._filter_news_by_time(all_news, start_time, end_time)

            self.logger.info(f"筛选出 {len(filtered_news)} 条新闻")

            if filtered_news:
                self._send_summary(filtered_news, f"早间总结 - {today.strftime('%Y-%m-%d')}")
            else:
                self.logger.warning("没有符合条件的新闻，跳过发送")

        except Exception as e:
            self.logger.error(f"早上总结任务异常: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _evening_summary(self):
        """晚上 21:00 发送总结"""
        now = datetime.now(self.china_tz)
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"执行晚上总结任务 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"{'=' * 60}")

        try:
            # 计算时间范围: 今天 08:30 至晚上 21:00
            today = now.date()

            start_time = self.china_tz.localize(datetime.combine(today, datetime.min.time().replace(hour=8, minute=30)))
            end_time = now

            self.logger.info(f"总结时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # 加载新闻
            all_news = self.data_manager.load_news('财联社')
            filtered_news = self._filter_news_by_time(all_news, start_time, end_time)

            self.logger.info(f"筛选出 {len(filtered_news)} 条新闻")

            if filtered_news:
                self._send_summary(filtered_news, f"晚间总结 - {today.strftime('%Y-%m-%d')}")
            else:
                self.logger.warning("没有符合条件的新闻，跳过发送")

        except Exception as e:
            self.logger.error(f"晚上总结任务异常: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _filter_news_by_time(self, news_list: List[Dict[str, Any]], start_time, end_time) -> List[Dict[str, Any]]:
        """
        按时间范围过滤新闻

        Args:
            news_list: 新闻列表
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            过滤后的新闻列表
        """
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
                    publish_time = self.china_tz.localize(publish_time)

                # 检查是否在时间范围内
                if start_time <= publish_time <= end_time:
                    filtered_news.append(news)

            except Exception as e:
                self.logger.warning(f"解析新闻时间失败: {e}")
                continue

        return filtered_news

    def _send_summary(self, news_list: List[Dict[str, Any]], title: str):
        """
        发送新闻总结

        Args:
            news_list: 新闻列表
            title: 总结标题
        """
        self.logger.info(f"开始发送总结: {title}")

        # 分类新闻
        classified_news = classify_news_list(news_list)
        self.logger.info(f"分类完成: {len(classified_news)} 个分类")

        # 发送邮件总结
        if 'email' in self.notifiers:
            try:
                notifier = self.notifiers['email']
                # 创建每日总结邮件推送器
                summary_notifier = DailySummaryEmailNotifier(
                    smtp_host=notifier.smtp_host,
                    smtp_port=notifier.smtp_port,
                    sender=notifier.sender,
                    password=notifier.password,
                    recipients=notifier.recipients,
                    use_tls=notifier.use_tls
                )
                date_str = datetime.now(self.china_tz).strftime('%Y-%m-%d')
                success = summary_notifier.send_daily_summary(classified_news, date_str, len(news_list))
                if success:
                    self.logger.info("邮件总结发送成功")
                else:
                    self.logger.warning("邮件总结发送失败")
            except Exception as e:
                self.logger.error(f"邮件总结发送异常: {e}")
                import traceback
                self.logger.error(traceback.format_exc())

        # 发送企业微信总结
        if 'wechat' in self.notifiers:
            try:
                notifier = self.notifiers['wechat']
                success = notifier.send(news_list, source=title)
                if success:
                    self.logger.info("企业微信总结发送成功")
                else:
                    self.logger.warning("企业微信总结发送失败")
            except Exception as e:
                self.logger.error(f"企业微信总结发送异常: {e}")
                import traceback
                self.logger.error(traceback.format_exc())


def main():
    """主函数"""
    try:
        app = SchedulerApp()
        app.run()
    except Exception as e:
        logger = Logger.get_logger('scheduler')
        logger.critical(f"应用异常: {e}")
        import traceback
        logger.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
