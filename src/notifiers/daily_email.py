"""
每日新闻总结邮件推送器
继承自 EmailNotifier，提供专用的每日总结邮件模板
"""
from typing import List, Dict, Any
from datetime import datetime
from .email import EmailNotifier
from ..utils.classifier import DAILY_CATEGORIES


class DailySummaryEmailNotifier(EmailNotifier):
    """每日新闻总结邮件推送器"""

    def send_daily_summary(
        self,
        classified_news: Dict[str, List[Dict[str, Any]]],
        date_str: str,
        total_count: int
    ) -> bool:
        """
        发送每日总结邮件

        Args:
            classified_news: 分类后的新闻字典 {category: [news_list]}
            date_str: 日期字符串，格式 YYYY-MM-DD
            total_count: 当天总新闻数

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
            msg = self._build_daily_email(classified_news, date_str, total_count)

            # 连接 SMTP 服务器
            if self.use_tls:
                server = self.smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
            else:
                server = self.smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)

            # 登录
            server.login(self.sender, self.password)

            # 发送邮件
            server.send_message(msg)
            server.quit()

            print(f"[{self.name}] 每日总结推送成功 ({date_str}): {total_count} 条新闻 -> {', '.join(self.recipients)}")
            return True

        except Exception as e:
            print(f"[{self.name}] 每日总结推送异常: {e}")
            return False

    def _build_daily_email(
        self,
        classified_news: Dict[str, List[Dict[str, Any]]],
        date_str: str,
        total_count: int
    ):
        """
        构建每日总结邮件

        Args:
            classified_news: 分类后的新闻字典
            date_str: 日期字符串
            total_count: 总新闻数

        Returns:
            MIMEMultipart 对象
        """
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'A股每日新闻总结 - 财联社 | {date_str} ({total_count}条)'
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)

        # 构建 HTML 内容
        html_content = self._build_daily_html(classified_news, date_str, total_count)

        # 添加 HTML 部分
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        return msg

    def _build_daily_html(
        self,
        classified_news: Dict[str, List[Dict[str, Any]]],
        date_str: str,
        total_count: int
    ) -> str:
        """
        构建每日总结 HTML 邮件内容

        Args:
            classified_news: 分类后的新闻字典
            date_str: 日期字符串
            total_count: 总新闻数

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
            '.news-title { color: #333; font-size: 14px; line-height: 1.5; margin-bottom: 5px; }',
            '.news-link { display: inline-block; color: #667eea; text-decoration: none; font-size: 12px; }',
            '.news-link:hover { text-decoration: underline; }',
            '.more-news { color: #999; font-size: 12px; font-style: italic; padding: 10px 0; }',
            '.footer { padding: 20px; background-color: #f9f9f9; border-top: 1px solid #eee; text-align: center; color: #999; font-size: 12px; }',
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
            f'<p>日期：{date_str} | 总计：{total_count}条</p>',
            '</div>',
        ])

        # 2. 概览卡片
        html_lines.extend(self._build_overview_section(classified_news))

        # 3. 分类详情
        html_lines.append('<div class="content">')
        for category, news_list in classified_news.items():
            html_lines.extend(self._build_category_section(category, news_list))
        html_lines.append('</div>')

        # 4. 页脚
        html_lines.extend([
            '<div class="footer">',
            f'<p>生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
            '<p>数据来源：财联社 | 自动生成，仅供参考</p>',
            '</div>',
            '</div>',
            '</body>',
            '</html>',
        ])

        return '\n'.join(html_lines)

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

        # 按发布时间倒序排列（最新的在前）
        sorted_news = sorted(
            news_list,
            key=lambda x: x.get('publish_time', ''),
            reverse=True
        )

        # 显示前 max_display 条
        for news in sorted_news[:max_display]:
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

            url_html = f'<a href="{url}" class="news-link" target="_blank">查看详情</a>' if url else ''

            html_lines.append(
                f'<div class="news-item">'
                f'<span class="news-time">{time_str}</span>'
                f'<div class="news-content">'
                f'<div class="news-title">{title}</div>'
                f'{url_html}'
                f'</div>'
                f'</div>'
            )

        # 如果超过 max_display 条，显示提示
        if len(sorted_news) > max_display:
            html_lines.append(
                f'<div class="more-news">本分类共 {len(sorted_news)} 条，仅展示前 {max_display} 条</div>'
            )

        html_lines.extend([
            '</div>',
            '</div>',
        ])

        return html_lines
