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
            'h2 { color: #ff6600; margin-top: 20px; }',
            '.summary { background-color: #fff3cd; padding: 15px; border-left: 4px solid #ff6600; margin: 20px 0; }',
            '.summary-item { margin: 8px 0; }',
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
        ]

        # 添加热点总结
        summary = self._generate_summary(news_list)
        if summary:
            html_lines.append('<div class="summary">')
            html_lines.append('<h2>🔥 热点总结</h2>')
            for item in summary:
                html_lines.append(f'<div class="summary-item">{item}</div>')
            html_lines.append('</div>')

        html_lines.extend([
            '<table>',
            '<tr>',
            '<th>时间</th>',
            '<th>标题</th>',
            '<th>链接</th>',
            '</tr>',
        ])

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
                            sector_examples[sector] = title[:40]
                        break

        # 获取前3个热点板块
        sorted_sectors = sorted(sector_count.items(), key=lambda x: x[1], reverse=True)[:3]

        summary_lines = []
        for idx, (sector, count) in enumerate(sorted_sectors, 1):
            example = sector_examples.get(sector, '')
            summary_lines.append(f"{idx}. <strong>{sector}</strong> ({count}条) - {example}...")

        return summary_lines
