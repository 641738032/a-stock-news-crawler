"""
邮箱推送模块
通过 SMTP 发送邮件
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from .base import BaseNotifier


class EmailNotifier(BaseNotifier):
    """邮箱推送器"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender: str,
        password: str,
        recipients: List[str],
        use_tls: bool = True
    ):
        """
        初始化邮箱推送器

        Args:
            smtp_host: SMTP 服务器地址
            smtp_port: SMTP 端口
            sender: 发件人邮箱
            password: 邮箱密码/授权码
            recipients: 收件人列表
            use_tls: 是否使用 TLS
        """
        super().__init__(name='邮箱')
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender = sender
        self.password = password
        self.recipients = recipients if isinstance(recipients, list) else [recipients]
        self.use_tls = use_tls

    def send(self, news_list: List[Dict[str, Any]], source: str = '', watchlist_news: List[Dict[str, Any]] = None) -> bool:
        """
        发送邮件

        Args:
            news_list: 新闻列表
            source: 数据源名称

        Returns:
            是否发送成功
        """
        if not news_list:
            print(f"[{self.name}] 没有新闻需要推送")
            return True

        if not self.recipients:
            print(f"[{self.name}] 收件人未配置")
            return False

        try:
            # 构建邮件
            msg = self._build_email(news_list, source, watchlist_news or [])

            # 连接 SMTP 服务器
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)

            # 登录
            server.login(self.sender, self.password)

            # 发送邮件
            server.send_message(msg)
            server.quit()

            print(f"[{self.name}] 推送成功 ({source}): {len(news_list)} 条新闻 -> {', '.join(self.recipients)}")
            return True

        except Exception as e:
            print(f"[{self.name}] 推送异常: {e}")
            return False

    def _build_email(self, news_list: List[Dict[str, Any]], source: str = '', watchlist_news: List[Dict[str, Any]] = None) -> MIMEMultipart:
        """
        构建邮件

        Args:
            news_list: 新闻列表
            source: 数据源名称

        Returns:
            MIMEMultipart 对象
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'A股新闻播报 - {source} ({len(news_list)} 条新闻)'
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)

        # 构建 HTML 内容
        html_content = self._build_html(news_list, source, watchlist_news or [])

        # 添加 HTML 部分
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        return msg

    def _build_html(self, news_list: List[Dict[str, Any]], source: str = '', watchlist_news: List[Dict[str, Any]] = None) -> str:
        """
        构建 HTML 邮件内容

        Args:
            news_list: 新闻列表
            source: 数据源名称

        Returns:
            HTML 字符串
        """
        from datetime import datetime
        import pytz

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
            '.content { padding: 20px; }',
            '.news-item { padding: 12px 0; border-bottom: 1px solid #eee; display: flex; gap: 10px; }',
            '.news-item:last-child { border-bottom: none; }',
            '.news-time { color: #999; font-size: 12px; white-space: nowrap; min-width: 50px; }',
            '.news-content { flex: 1; }',
            '.news-title { color: #333; font-size: 14px; line-height: 1.5; margin-bottom: 5px; font-weight: bold; }',
            '.news-snippet { color: #666; font-size: 13px; line-height: 1.6; margin-bottom: 8px; }',
            '.news-meta { display: flex; gap: 15px; margin-bottom: 8px; font-size: 12px; }',
            '.news-tags { color: #667eea; }',
            '.news-tags::before { content: "标签: "; color: #999; }',
            '.news-link { display: inline-block; color: #667eea; text-decoration: none; font-size: 12px; }',
            '.news-link:hover { text-decoration: underline; }',
            '.footer { padding: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center; }',
            '.footer p { margin: 5px 0; }',
            '@media only screen and (max-width: 600px) {',
            '  .news-item { flex-direction: column; gap: 5px; }',
            '  .news-time { min-width: auto; }',
            '}',
            '</style>',
            '</head>',
            '<body>',
            '<div class="container">',
            '<div class="header">',
            '<h1>📰 A股新闻播报</h1>',
            f'<p>来源：{source} | 共 {len(news_list)} 条新闻</p>',
            '</div>',
        ]

        # 生成摘要并排序
        from ..utils.summary_generator import SummaryGenerator
        summary_generator = SummaryGenerator()
        summaries = summary_generator.generate_summaries(news_list)

        # 持股仓关注模块
        if watchlist_news:
            html_lines.extend([
                '<div style="padding:20px;background-color:#f0fff4;border-left:4px solid #27ae60;margin:20px 0;">',
                '<h2 style="margin:0 0 15px 0;font-size:18px;color:#27ae60;">⭐ 持股仓关注</h2>',
            ])
            wl_summaries = summary_generator.generate_summaries(watchlist_news)
            for idx, s in enumerate(wl_summaries, 1):
                url_html = f'<a href="{s.url}" style="color:#667eea;text-decoration:none;font-size:12px;" target="_blank">查看详情</a>' if s.url else ''
                html_lines.append(
                    f'<div style="padding:10px 0;border-bottom:1px solid #c3e6cb;">'
                    f'<div style="font-size:14px;font-weight:bold;color:#333;margin-bottom:4px;">{idx}. {s.title}</div>'
                    f'<div style="font-size:13px;color:#666;margin-bottom:6px;">{s.snippet}</div>'
                    f'{url_html}'
                    f'</div>'
                )
            html_lines.append('</div>')

        # 添加热点列表（Top 10）
        html_lines.extend([
            '<div class="hotspot-section">',
            '<h2>🔥 热点新闻 Top 10</h2>',
            '<div class="hotspot-list">',
        ])

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

        # 添加所有新闻列表
        html_lines.extend([
            '<div class="content">',
            '<h2>📋 全部新闻</h2>',
            '<div class="news-list">',
        ])

        for idx, summary in enumerate(summaries[:50], 1):  # 最多显示 50 条
            title = summary.title
            url = summary.url
            time_str = summary.get_time_str()
            tags_str = summary.get_tags_str()
            snippet = summary.snippet

            url_html = f'<a href="{url}" class="news-link" target="_blank">查看详情</a>' if url else ''

            html_lines.append(
                f'<div class="news-item">'
                f'<span class="news-time">{time_str}</span>'
                f'<div class="news-content">'
                f'<div class="news-title">{idx}. {title}</div>'
                f'<div class="news-snippet">{snippet}</div>'
                f'<div class="news-meta">'
                f'<span class="news-tags">{tags_str}</span>'
                f'</div>'
                f'{url_html}'
                f'</div>'
                f'</div>'
            )

        html_lines.extend([
            '</div>',
            '</div>',
        ])

        # 页脚
        china_tz = pytz.timezone('Asia/Shanghai')
        html_lines.extend([
            '<div class="footer">',
            f'<p>发送时间：{datetime.now(china_tz).strftime("%Y-%m-%d %H:%M:%S")}</p>',
            '<p>数据来源：财联社 | 自动生成，仅供参考</p>',
            '</div>',
            '</div>',
            '</body>',
            '</html>',
        ])

        return '\n'.join(html_lines)

