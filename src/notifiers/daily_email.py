"""
每日新闻总结邮件推送器
继承自 EmailNotifier，提供专用的每日总结邮件模板
"""
import smtplib
from typing import List, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz
from .email import EmailNotifier
from ..utils.classifier import DAILY_CATEGORIES
from ..utils.summary_generator import SummaryGenerator


class DailySummaryEmailNotifier(EmailNotifier):
    """每日新闻总结邮件推送器"""

    def send_daily_summary(
        self,
        classified_news: Dict[str, List[Dict[str, Any]]],
        date_str: str,
        total_count: int,
        period_name: str = "当天",
        watchlist_news: List[Dict[str, Any]] = None
    ) -> bool:
        """
        发送每日总结邮件

        Args:
            classified_news: 分类后的新闻字典 {category: [news_list]}
            date_str: 日期字符串，格式 YYYY-MM-DD
            total_count: 当天总新闻数
            period_name: 时间段名称

        Returns:
            是否发送成功
        """
        if not classified_news:
            print(f"[{self.name}] 没有分类新闻需要推送")
            return True

        if not self.recipients:
            print(f"[{self.name}] 收件人未配置")
            return False

        try:
            # 构建邮件
            msg = self._build_daily_email(classified_news, date_str, total_count, period_name, watchlist_news or [])
            print(f"[{self.name}] 邮件构建完成，大小: {len(msg.as_string())} 字节")

            # 连接 SMTP 服务器
            print(f"[{self.name}] 正在连接 SMTP 服务器: {self.smtp_host}:{self.smtp_port} (TLS={self.use_tls})")
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                print(f"[{self.name}] SMTP 连接成功，正在启用 TLS")
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
                print(f"[{self.name}] SMTP_SSL 连接成功")

            # 登录
            print(f"[{self.name}] 正在登录: {self.sender}")
            server.login(self.sender, self.password)
            print(f"[{self.name}] 登录成功")

            # 发送邮件
            print(f"[{self.name}] 正在发送邮件到: {', '.join(self.recipients)}")
            server.send_message(msg)
            print(f"[{self.name}] 邮件发送成功")

            server.quit()
            print(f"[{self.name}] SMTP 连接已关闭")

            print(f"[{self.name}] 每日总结推送成功 ({date_str}): {total_count} 条新闻 -> {', '.join(self.recipients)}")
            return True

        except Exception as e:
            import traceback
            print(f"[{self.name}] 每日总结推送异常: {e}")
            print(f"[{self.name}] 错误详情:\n{traceback.format_exc()}")
            return False

    def _build_daily_email(
        self,
        classified_news: Dict[str, List[Dict[str, Any]]],
        date_str: str,
        total_count: int,
        period_name: str = "当天",
        watchlist_news: List[Dict[str, Any]] = None
    ):
        """
        构建每日总结邮件

        Args:
            classified_news: 分类后的新闻字典
            date_str: 日期字符串
            total_count: 总新闻数
            period_name: 时间段名称

        Returns:
            MIMEMultipart 对象
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'A股每日新闻总结 - 财联社 | {date_str} ({period_name}) ({total_count}条)'
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)

        # 构建 HTML 内容
        html_content = self._build_daily_html(classified_news, date_str, total_count, period_name, watchlist_news or [])

        # 添加 HTML 部分
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        return msg

    def _build_daily_html(
        self,
        classified_news: Dict[str, List[Dict[str, Any]]],
        date_str: str,
        total_count: int,
        period_name: str = "当天",
        watchlist_news: List[Dict[str, Any]] = None
    ) -> str:
        """
        构建每日总结 HTML 邮件内容

        Args:
            classified_news: 分类后的新闻字典
            date_str: 日期字符串
            total_count: 总新闻数
            period_name: 时间段名称

        Returns:
            HTML 字符串
        """
        html_lines = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<style>',
            'body { font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }',
            '.container { max-width: 800px; margin: 0 auto; background-color: white; }',
            '.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }',
            '.header h1 { margin: 0 0 10px 0; font-size: 28px; }',
            '.header p { margin: 5px 0; font-size: 14px; opacity: 0.9; }',
            '.overview { padding: 20px; background-color: #f9f9f9; border-bottom: 1px solid #eee; }',
            '.overview h2 { margin: 0 0 15px 0; font-size: 18px; color: #333; }',
            '.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }',
            '.stat-item { padding: 12px; background-color: white; border-radius: 4px; border-left: 4px solid #667eea; }',
            '.stat-item .badge { display: inline-block; padding: 4px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; color: white; margin-right: 8px; }',
            '.stat-item .count { font-size: 18px; font-weight: bold; color: #333; }',
            '.content { padding: 20px; }',
            '.category-section { margin-bottom: 30px; }',
            '.category-header { display: flex; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid; }',
            '.category-header h3 { margin: 0; font-size: 18px; }',
            '.category-header .count { margin-left: auto; font-size: 14px; color: #999; }',
            '.news-list { }',
            '.news-item { padding: 12px 0; border-bottom: 1px solid #eee; display: flex; gap: 10px; }',
            '.news-item:last-child { border-bottom: none; }',
            '.news-time { color: #999; font-size: 12px; white-space: nowrap; min-width: 50px; }',
            '.news-content { flex: 1; }',
            '.news-title { color: #333; font-size: 14px; line-height: 1.5; margin-bottom: 5px; font-weight: bold; }',
            '.news-snippet { color: #666; font-size: 13px; line-height: 1.6; margin-bottom: 8px; }',
            '.news-meta { display: flex; gap: 15px; margin-bottom: 8px; font-size: 12px; }',
            '.news-tags { color: #667eea; }',
            '.news-tags::before { content: "标签: "; color: #999; }',
            '.news-reason { color: #ff6b6b; }',
            '.news-reason::before { content: "理由: "; color: #999; }',
            '.news-link { display: inline-block; color: #667eea; text-decoration: none; font-size: 12px; }',
            '.news-link:hover { text-decoration: underline; }',
            '.more-news { color: #999; font-size: 12px; font-style: italic; padding: 10px 0; }',
            '.hotspot-section { padding: 20px; background-color: #fff8f0; border-left: 4px solid #ff6b6b; margin: 20px 0; }',
            '.hotspot-section h2 { margin: 0 0 15px 0; font-size: 18px; color: #ff6b6b; }',
            '.hotspot-list { }',
            '.hotspot-item { padding: 12px 0; border-bottom: 1px solid #ffe0d6; display: flex; gap: 10px; }',
            '.hotspot-item:last-child { border-bottom: none; }',
            '.hotspot-rank { color: #ff6b6b; font-weight: bold; font-size: 16px; min-width: 30px; }',
            '.hotspot-content { flex: 1; }',
            '.hotspot-title { color: #333; font-size: 14px; line-height: 1.5; margin-bottom: 5px; font-weight: bold; }',
            '.hotspot-snippet { color: #666; font-size: 13px; line-height: 1.6; margin-bottom: 8px; }',
            '.hotspot-meta { display: flex; gap: 15px; font-size: 12px; }',
            '.hotspot-score { color: #ff6b6b; }',
            '.hotspot-score::before { content: "热度: "; color: #999; }',
            '.hotspot-link { color: #667eea; text-decoration: none; }',
            '.hotspot-link:hover { text-decoration: underline; }',
            '.highlights-section { padding: 20px; background-color: #f0f8ff; border-left: 4px solid #667eea; margin: 20px 0; }',
            '.highlights-section h2 { margin: 0 0 15px 0; font-size: 18px; color: #667eea; }',
            '.highlight-item { padding: 12px 0; border-bottom: 1px solid #d6e8ff; }',
            '.highlight-item:last-child { border-bottom: none; }',
            '.highlight-title { color: #333; font-size: 14px; line-height: 1.5; margin-bottom: 5px; font-weight: bold; }',
            '.highlight-reason { color: #667eea; font-size: 13px; margin-bottom: 8px; }',
            '.highlight-reason::before { content: "💡 "; }',
            '.highlight-link { color: #667eea; text-decoration: none; font-size: 12px; }',
            '.highlight-link:hover { text-decoration: underline; }',
            '.footer p { margin: 5px 0; }',
            '@media only screen and (max-width: 600px) {',
            '  .stats-grid { grid-template-columns: 1fr; }',
            '  .news-item { flex-direction: column; gap: 5px; }',
            '  .news-time { min-width: auto; }',
            '}',
            '</style>',
            '</head>',
            '<body>',
        ]

        # 1. 头部
        html_lines.extend([
            '<div class="container">',
            '<div class="header">',
            '<h1>📊 A股每日新闻总结</h1>',
            f'<p>日期：{date_str} | 时间段：{period_name} | 总计：{total_count}条</p>',
            '</div>',
        ])

        # 2. 概览卡片
        html_lines.extend(self._build_overview_section(classified_news))

        # 3. 持股仓关注
        if watchlist_news:
            html_lines.extend(self._build_watchlist_section(watchlist_news))

        # 4. 热点列表（Top 5-10）
        html_lines.extend(self._build_hotspot_section(classified_news))

        # 4. 值得关注（Highlights）
        html_lines.extend(self._build_highlights_section(classified_news))

        # 5. 分类详情
        html_lines.append('<div class="content">')
        for category, news_list in classified_news.items():
            html_lines.extend(self._build_category_section(category, news_list))
        html_lines.append('</div>')

        # 4. 页脚
        china_tz = pytz.timezone('Asia/Shanghai')
        html_lines.extend([
            '<div class="footer">',
            f'<p>生成时间：{datetime.now(china_tz).strftime("%Y-%m-%d %H:%M:%S")}</p>',
            '<p>数据来源：财联社 | 自动生成，仅供参考</p>',
            '</div>',
            '</div>',
            '</body>',
            '</html>',
        ])

        return '\n'.join(html_lines)

    def _build_watchlist_section(self, watchlist_news: List[Dict[str, Any]]) -> List[str]:
        """构建持股仓关注区块"""
        from ..utils.summary_generator import SummaryGenerator

        html_lines = [
            '<div style="padding:20px;background-color:#f0fff4;border-left:4px solid #27ae60;margin:20px 0;">',
            '<h2 style="margin:0 0 15px 0;font-size:18px;color:#27ae60;">⭐ 持股仓关注</h2>',
        ]

        summary_generator = SummaryGenerator()
        summaries = summary_generator.generate_summaries(watchlist_news)

        for idx, s in enumerate(summaries, 1):
            url_html = f'<a href="{s.url}" style="color:#667eea;text-decoration:none;font-size:12px;" target="_blank">查看详情</a>' if s.url else ''
            time_str = s.get_time_str()
            html_lines.append(
                f'<div style="padding:10px 0;border-bottom:1px solid #c3e6cb;">'
                f'<div style="font-size:14px;font-weight:bold;color:#333;margin-bottom:4px;">{idx}. {s.title}</div>'
                f'<div style="font-size:13px;color:#666;margin-bottom:6px;">{s.snippet}</div>'
                f'<div style="font-size:12px;color:#999;margin-bottom:4px;">{time_str}</div>'
                f'{url_html}'
                f'</div>'
            )

        html_lines.append('</div>')
        return html_lines

    def _build_overview_section(self, classified_news: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """
        构建概览卡片区块

        Args:
            classified_news: 分类后的新闻字典

        Returns:
            HTML 行列表
        """
        html_lines = [
            '<div class="overview">',
            '<h2>📈 今日概览</h2>',
            '<div class="stats-grid">',
        ]

        # 按新闻数量降序排列
        sorted_categories = sorted(
            classified_news.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        for category, news_list in sorted_categories:
            config = DAILY_CATEGORIES.get(category, {})
            color = config.get('color', '#667eea')
            count = len(news_list)

            html_lines.append(
                f'<div class="stat-item">'
                f'<span class="badge" style="background-color: {color};">{category}</span>'
                f'<span class="count">{count}条</span>'
                f'</div>'
            )

        html_lines.extend([
            '</div>',
            '</div>',
        ])

        return html_lines

    def _build_hotspot_section(self, classified_news: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """
        构建热点列表区块（Top 5-10）

        Args:
            classified_news: 分类后的新闻字典

        Returns:
            HTML 行列表
        """
        from ..utils.summary_generator import SummaryGenerator

        html_lines = [
            '<div class="hotspot-section">',
            '<h2>🔥 热点新闻 Top 10</h2>',
            '<div class="hotspot-list">',
        ]

        # 收集所有新闻并生成摘要
        all_news = []
        for category, news_list in classified_news.items():
            all_news.extend(news_list)

        # 生成摘要并排序
        summary_generator = SummaryGenerator()
        summaries = summary_generator.generate_summaries(all_news)

        # 显示前10条
        for idx, summary in enumerate(summaries[:10], 1):
            title = summary.title
            url = summary.url
            score = summary.score
            snippet = summary.snippet

            url_html = f'<a href="{url}" class="hotspot-link" target="_blank">查看详情</a>' if url else ''

            html_lines.append(
                f'<div class="hotspot-item">'
                f'<span class="hotspot-rank">{idx}</span>'
                f'<div class="hotspot-content">'
                f'<div class="hotspot-title">{title}</div>'
                f'<div class="hotspot-snippet">{snippet}</div>'
                f'<div class="hotspot-meta">'
                f'<span class="hotspot-score">{score:.0f}</span>'
                f'{url_html}'
                f'</div>'
                f'</div>'
                f'</div>'
            )

        html_lines.extend([
            '</div>',
            '</div>',
        ])

        return html_lines

    def _build_highlights_section(self, classified_news: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """
        构建值得关注区块（Highlights）

        Args:
            classified_news: 分类后的新闻字典

        Returns:
            HTML 行列表
        """
        from ..utils.summary_generator import SummaryGenerator

        html_lines = [
            '<div class="highlights-section">',
            '<h2>💡 值得关注</h2>',
        ]

        # 收集所有新闻并生成摘要
        all_news = []
        for category, news_list in classified_news.items():
            all_news.extend(news_list)

        # 生成摘要并排序
        summary_generator = SummaryGenerator()
        summaries = summary_generator.generate_summaries(all_news)

        # 选择热度最高的3条
        highlights = summaries[:3]

        if not highlights:
            html_lines.append('<p>暂无特别重要的新闻</p>')
        else:
            for summary in highlights:
                title = summary.title
                url = summary.url
                reason = summary.reason or summary.category
                snippet = summary.snippet

                url_html = f'<a href="{url}" class="highlight-link" target="_blank">查看详情</a>' if url else ''

                html_lines.append(
                    f'<div class="highlight-item">'
                    f'<div class="highlight-title">{title}</div>'
                    f'<div class="highlight-reason">{reason}</div>'
                    f'<div class="highlight-snippet">{snippet}</div>'
                    f'{url_html}'
                    f'</div>'
                )

        html_lines.extend([
            '</div>',
        ])

        return html_lines

    def _build_category_section(
        self,
        category: str,
        news_list: List[Dict[str, Any]],
        max_display: int = 20
    ) -> List[str]:
        """
        构建单个分类区块

        Args:
            category: 分类名称
            news_list: 该分类的新闻列表
            max_display: 最多显示的新闻数

        Returns:
            HTML 行列表
        """
        config = DAILY_CATEGORIES.get(category, {})
        color = config.get('color', '#667eea')

        html_lines = [
            '<div class="category-section">',
            f'<div class="category-header" style="border-bottom-color: {color};">',
            f'<h3 style="color: {color};">🔹 {category}</h3>',
            f'<span class="count">共 {len(news_list)} 条</span>',
            '</div>',
            '<div class="news-list">',
        ]

        # 生成摘要
        summary_generator = SummaryGenerator()
        summaries = summary_generator.generate_summaries(news_list)

        # 显示前 max_display 条
        for idx, summary in enumerate(summaries[:max_display], 1):
            title = summary.title
            url = summary.url
            time_str = summary.get_time_str()
            tags_str = summary.get_tags_str()
            snippet = summary.snippet
            reason = summary.reason

            url_html = f'<a href="{url}" class="news-link" target="_blank">查看详情</a>' if url else ''

            # 构建新闻项 HTML
            html_lines.append(
                f'<div class="news-item">'
                f'<span class="news-time">{time_str}</span>'
                f'<div class="news-content">'
                f'<div class="news-title">{idx}. {title}</div>'
                f'<div class="news-snippet">{snippet}</div>'
                f'<div class="news-meta">'
                f'<span class="news-tags">{tags_str}</span>'
                f'<span class="news-reason">{reason}</span>'
                f'</div>'
                f'{url_html}'
                f'</div>'
                f'</div>'
            )

        # 如果超过 max_display 条，显示提示
        if len(summaries) > max_display:
            html_lines.append(
                f'<div class="more-news">本分类共 {len(summaries)} 条，仅展示前 {max_display} 条</div>'
            )

        html_lines.extend([
            '</div>',
            '</div>',
        ])

        return html_lines
