#!/usr/bin/env python3
"""
推送器测试脚本
用于测试企业微信和邮箱推送功能
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.notifiers.wechat import WeChatNotifier
from src.notifiers.email import EmailNotifier


def test_wechat():
    """测试企业微信推送"""
    print("=" * 60)
    print("测试企业微信推送")
    print("=" * 60)

    webhook_url = os.getenv('WECHAT_WEBHOOK_URL')
    if not webhook_url:
        print("❌ WECHAT_WEBHOOK_URL 未配置")
        return False

    notifier = WeChatNotifier(webhook_url)

    # 构造测试数据
    test_news = [
        {
            'title': '【测试】财联社快讯 - 这是一条测试消息',
            'content': '这是测试内容',
            'url': 'https://www.cls.cn/telegraph/1',
            'publish_time': '2026-01-26 10:30:00'
        },
        {
            'title': '【测试】雪球话题 - 另一条测试消息',
            'content': '测试内容2',
            'url': 'https://xueqiu.com/test',
            'publish_time': '2026-01-26 10:35:00'
        }
    ]

    success = notifier.send(test_news, source='财联社')
    if success:
        print("✅ 企业微信推送成功")
    else:
        print("❌ 企业微信推送失败")

    return success


def test_email():
    """测试邮箱推送"""
    print("\n" + "=" * 60)
    print("测试邮箱推送")
    print("=" * 60)

    smtp_host = os.getenv('EMAIL_SMTP_HOST')
    smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
    sender = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')

    if not all([smtp_host, sender, password, recipients]):
        print("❌ 邮箱配置不完整")
        print(f"   SMTP_HOST: {smtp_host}")
        print(f"   EMAIL_USER: {sender}")
        print(f"   EMAIL_PASSWORD: {'*' * len(password) if password else '未配置'}")
        print(f"   EMAIL_RECIPIENTS: {recipients}")
        return False

    notifier = EmailNotifier(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        sender=sender,
        password=password,
        recipients=recipients,
        use_tls=True
    )

    # 构造测试数据
    test_news = [
        {
            'title': '【测试】财联社快讯 - 这是一条测试消息',
            'content': '这是测试内容',
            'url': 'https://www.cls.cn/telegraph/1',
            'publish_time': '2026-01-26 10:30:00'
        },
        {
            'title': '【测试】雪球话题 - 另一条测试消息',
            'content': '测试内容2',
            'url': 'https://xueqiu.com/test',
            'publish_time': '2026-01-26 10:35:00'
        }
    ]

    success = notifier.send(test_news, source='财联社')
    if success:
        print("✅ 邮箱推送成功")
    else:
        print("❌ 邮箱推送失败")

    return success


def main():
    """主函数"""
    print("\n🧪 推送器测试\n")

    wechat_ok = test_wechat()
    email_ok = test_email()

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"企业微信: {'✅ 成功' if wechat_ok else '❌ 失败'}")
    print(f"邮箱:    {'✅ 成功' if email_ok else '❌ 失败'}")
    print("=" * 60)

    if wechat_ok or email_ok:
        print("\n✅ 至少一个推送器工作正常")
        return 0
    else:
        print("\n❌ 所有推送器都失败了")
        return 1


if __name__ == '__main__':
    sys.exit(main())
