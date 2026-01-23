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

    def send(self, news_list: List[Dict[str, Any]], source: str = '') -> bool:
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
            msg = self._build_email(news_list, source)

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

    def _build_email(self, news_list: List[Dict[str, Any]], source: str = '') -> MIMEMultipart:
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
        html_content = self._build_html(news_list, source)

        # 添加 HTML 部分
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        return msg

    def _build_html(self, news_list: List[Dict[str, Any]], source: str = '') -> str:
        """
        构建 HTML 邮件内容

        Args:
            news_list: 新闻列表
            source: 数据源名称

        Returns:
            HTML 字符串
        """
        from datetime import datetime

        html_lines = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="utf-8">',
            '<style>',
            'body { font-family: Arial, sans-serif; color: #333; }',
            'h1 { color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }',
            'table { width: 100%; border-collapse: collapse; margin-top: 20px; }',
            'th { background-color: #0066cc; color: white; padding: 10px; text-align: left; }',
            'td { padding: 10px; border-bottom: 1px solid #ddd; }',
            'tr:hover { background-color: #f5f5f5; }',
            'a { color: #0066cc; text-decoration: none; }',
            'a:hover { text-decoration: underline; }',
            '.time { color: #999; font-size: 12px; }',
            '.footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }',
            '</style>',
            '</head>',
            '<body>',
            f'<h1>📰 A股新闻播报 - {source}</h1>',
            f'<p>共 <strong>{len(news_list)}</strong> 条新闻</p>',
            '<table>',
            '<tr>',
            '<th>时间</th>',
            '<th>标题</th>',
            '<th>链接</th>',
            '</tr>',
        ]

        for news in news_list[:50]:  # 最多显示 50 条
            title = news.get('title', '无标题')
            url = news.get('url', '')
            publish_time = news.get('publish_time', '')

            # 提取时间部分
            time_str = ''
            if publish_time:
                try:
                    dt = datetime.fromisoformat(publish_time)
                    time_str = dt.strftime('%H:%M')
                except:
                    pass

            url_html = f'<a href="{url}" target="_blank">查看</a>' if url else '-'

            html_lines.append('<tr>')
            html_lines.append(f'<td class="time">{time_str}</td>')
            html_lines.append(f'<td>{title}</td>')
            html_lines.append(f'<td>{url_html}</td>')
            html_lines.append('</tr>')

        html_lines.extend([
            '</table>',
            '<div class="footer">',
            f'<p>发送时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
            '<p>这是一封自动生成的邮件，请勿回复。</p>',
            '</div>',
            '</body>',
            '</html>',
        ])

        return '\n'.join(html_lines)
