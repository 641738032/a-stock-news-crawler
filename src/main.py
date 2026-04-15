"""
主程序
协调爬虫、数据管理、推送等模块
"""
import os
import sys
from typing import List, Dict, Any

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scrapers.cls_scraper_api import CLSScraperAPI
from src.scrapers.xueqiu_scraper_improved import XueqiuScraperImproved
from src.utils.data_manager import DataManager
from src.utils.time_utils import TimeUtils, get_trading_status
from src.utils.logger import Logger
from src.utils.watchlist import parse_watchlist, filter_watchlist_news, flatten_watchlist_tokens
from src.notifiers.wechat import WeChatNotifier
from src.notifiers.email import EmailNotifier


class CrawlerApp:
    """爬虫应用主类"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化爬虫应用

        Args:
            config: 配置字典
        """
        self.config = config or self._load_config()
        self.logger = Logger.get_logger()
        # 使用绝对路径确保数据保存到项目根目录
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.data_manager = DataManager(data_dir=data_dir)

        # 初始化爬虫 (使用 API 版本 - 直接调用 API)
        self.scrapers = {
            '财联社': CLSScraperAPI(),
            '雪球': XueqiuScraperImproved(),
        }

        # 初始化推送器
        self.notifiers = self._init_notifiers()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        import yaml
        import os

        config_file = 'config/config.yaml'
        if not os.path.exists(config_file):
            config_file = 'config/config.example.yaml'

        if not os.path.exists(config_file):
            self.logger.warning("配置文件不存在，使用默认配置")
            return self._get_default_config()

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置

        Returns:
            默认配置字典
        """
        return {
            'scrapers': {
                'cls': {'enabled': True},
                'xueqiu': {'enabled': True},
            },
            'notifiers': {
                'wechat': {'enabled': True},
                'email': {'enabled': True},
            },
            'schedule': {
                'trading_hours_only': False,
            }
        }

    def _init_notifiers(self) -> Dict[str, Any]:
        """
        初始化推送器

        Returns:
            推送器字典
        """
        notifiers = {}

        # 企业微信推送
        wechat_config = self.config.get('notifiers', {}).get('wechat', {})
        if wechat_config.get('enabled'):
            webhook_url = os.getenv('WECHAT_WEBHOOK_URL') or wechat_config.get('webhook_url')
            if webhook_url:
                notifiers['wechat'] = WeChatNotifier(webhook_url)
                self.logger.info("企业微信推送已启用")

        # 邮箱推送
        email_config = self.config.get('notifiers', {}).get('email', {})
        smtp_host = os.getenv('EMAIL_SMTP_HOST') or email_config.get('smtp_host')
        smtp_port_str = os.getenv('EMAIL_SMTP_PORT') or email_config.get('smtp_port', '587')
        sender = os.getenv('EMAIL_USER') or email_config.get('sender')
        password = os.getenv('EMAIL_PASSWORD') or email_config.get('password')
        recipients = os.getenv('EMAIL_RECIPIENTS') or email_config.get('recipients', '')

        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(',') if r.strip()]

        # 如果有环境变量或配置，则启用邮箱推送
        if smtp_host and sender and password and recipients:
            try:
                smtp_port = int(str(smtp_port_str).strip())
            except (ValueError, AttributeError):
                smtp_port = 587
                self.logger.warning(f"邮箱端口配置错误，使用默认端口 587")

            notifiers['email'] = EmailNotifier(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                sender=sender,
                password=password,
                recipients=recipients,
                use_tls=email_config.get('use_tls', True)
            )
            self.logger.info("邮箱推送已启用")
        elif email_config.get('enabled'):
            self.logger.warning("邮箱配置不完整，邮箱推送未启用")

        return notifiers

    def run(self):
        """
        运行爬虫应用
        """
        self.logger.info("=" * 50)
        self.logger.info("A股新闻爬虫启动")
        self.logger.info("=" * 50)

        # 检查交易时段
        is_trading, status = get_trading_status()
        self.logger.info(f"当前状态: {status}")

        # 如果配置了仅在交易时段运行，检查时间
        if self.config.get('schedule', {}).get('trading_hours_only', False):
            if not is_trading:
                self.logger.info("非交易时段，跳过爬取")
                return

        # 执行爬取
        all_new_items = {}
        for source_name, scraper in self.scrapers.items():
            # 只处理财联社
            if source_name != '财联社':
                self.logger.info(f"跳过 {source_name} (仅关注财联社)")
                continue

            if not self.config.get('scrapers', {}).get(source_name.lower(), {}).get('enabled', True):
                self.logger.info(f"跳过 {source_name} (已禁用)")
                continue

            self.logger.info(f"开始爬取 {source_name}...")
            try:
                # 爬取数据
                new_news = scraper.scrape()

                if not new_news:
                    self.logger.warning(f"{source_name} 爬取失败或无数据")
                    continue

                # 过滤最近一小时的新闻
                recent_news = self._filter_recent_news(new_news, hours=1)

                if recent_news:
                    all_new_items[source_name] = recent_news
                    self.logger.info(f"{source_name} 最近一小时新增 {len(recent_news)} 条新闻")

                # 合并数据
                merged_news = self.data_manager.merge_news(source_name, new_news)

                # 保存数据
                self.data_manager.save_news(source_name, merged_news)

            except Exception as e:
                self.logger.error(f"{source_name} 爬取异常: {e}")
                continue

        # 推送通知
        if all_new_items:
            watchlist = parse_watchlist()
            watchlist_tokens = flatten_watchlist_tokens(watchlist)
            if watchlist_tokens:
                self.logger.info(f"持股仓关键词已加载 ({len(watchlist_tokens)} 个): {', '.join(watchlist_tokens)}")
            else:
                self.logger.info("未配置 WATCHLIST_STOCKS，持股仓关注模块将不展示")
            self._send_notifications(all_new_items, watchlist)
        else:
            self.logger.info("没有最近一小时的新内容，跳过推送")

        # 输出统计信息
        stats = self.data_manager.get_statistics()
        self.logger.info(f"统计信息: {stats}")

        self.logger.info("=" * 50)
        self.logger.info("爬虫运行完成")
        self.logger.info("=" * 50)

    def _send_notifications(self, new_items: Dict[str, List[Dict[str, Any]]], watchlist: list = None):
        """
        发送推送通知

        Args:
            new_items: 新增项目字典 {source: [news_list]}
        """
        for source, news_list in new_items.items():
            self.logger.info(f"推送 {source} 的 {len(news_list)} 条新闻")

            wl_news = filter_watchlist_news(news_list, watchlist or [])
            self.logger.info(f"{source} 持股仓命中: {len(wl_news)} 条")
            for notifier_name, notifier in self.notifiers.items():
                try:
                    success = notifier.send(news_list, source=source, watchlist_news=wl_news)
                    if not success:
                        self.logger.warning(f"{notifier_name} 推送失败")
                except Exception as e:
                    self.logger.error(f"{notifier_name} 推送异常: {e}")

    def _filter_recent_news(self, news_list: List[Dict[str, Any]], hours: int = 1) -> List[Dict[str, Any]]:
        """
        过滤最近N小时的新闻

        Args:
            news_list: 新闻列表
            hours: 小时数

        Returns:
            过滤后的新闻列表
        """
        from datetime import datetime, timedelta
        import pytz

        # 使用北京时间
        china_tz = pytz.timezone('Asia/Shanghai')
        now_china = datetime.now(china_tz)
        cutoff_time = now_china - timedelta(hours=hours)

        self.logger.info(f"当前北京时间: {now_china.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"过滤截断时间: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")

        recent_news = []

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

                # 检查是否在最近N小时内
                if publish_time >= cutoff_time:
                    recent_news.append(news)
            except Exception as e:
                self.logger.warning(f"解析新闻时间失败: {e}")
                continue

        return recent_news


def main():
    """主函数"""
    try:
        app = CrawlerApp()
        app.run()
    except Exception as e:
        logger = Logger.get_logger()
        logger.critical(f"应用异常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
