#!/usr/bin/env python3
"""
GitHub Actions 测试脚本
用于在本地测试 GitHub Actions 工作流
"""
import subprocess
import sys

def test_github_actions():
    """测试 GitHub Actions 工作流"""
    print("=" * 60)
    print("GitHub Actions 工作流测试")
    print("=" * 60)

    print("\n📋 检查 GitHub CLI 是否已安装...")
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        print(f"✅ GitHub CLI 已安装: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ GitHub CLI 未安装")
        print("\n请先安装 GitHub CLI:")
        print("  macOS: brew install gh")
        print("  或访问: https://cli.github.com/")
        return False

    print("\n📋 检查 GitHub 认证状态...")
    try:
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub 认证成功")
        else:
            print("❌ GitHub 认证失败")
            print("\n请运行以下命令进行认证:")
            print("  gh auth login")
            return False
    except Exception as e:
        print(f"❌ 检查认证状态失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("手动触发 GitHub Actions 工作流")
    print("=" * 60)

    print("\n方法 1: 使用 GitHub CLI (推荐)")
    print("-" * 60)
    print("运行以下命令手动触发工作流:")
    print("\n  gh workflow run crawler.yml --ref main")
    print("\n然后查看运行状态:")
    print("  gh run list --workflow=crawler.yml")
    print("\n查看最新运行的详细日志:")
    print("  gh run view --log")

    print("\n方法 2: 使用 GitHub 网页界面")
    print("-" * 60)
    print("1. 打开你的 GitHub 仓库")
    print("2. 点击 'Actions' 标签")
    print("3. 选择 'A股新闻爬虫定时任务' 工作流")
    print("4. 点击 'Run workflow' 按钮")
    print("5. 选择分支 (main) 并点击 'Run workflow'")

    print("\n" + "=" * 60)
    print("验证 GitHub Secrets 配置")
    print("=" * 60)

    print("\n需要配置的 Secrets:")
    secrets = [
        'WECHAT_WEBHOOK_URL',
        'EMAIL_SMTP_HOST',
        'EMAIL_SMTP_PORT',
        'EMAIL_USER',
        'EMAIL_PASSWORD',
        'EMAIL_RECIPIENTS'
    ]

    for secret in secrets:
        print(f"  - {secret}")

    print("\n配置步骤:")
    print("1. 打开你的 GitHub 仓库")
    print("2. 点击 'Settings' → 'Secrets and variables' → 'Actions'")
    print("3. 点击 'New repository secret'")
    print("4. 输入 Secret 名称和值")
    print("5. 点击 'Add secret'")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n✅ 现在你可以手动触发 GitHub Actions 工作流了!")
    print("   工作流会使用你配置的 Secrets 来运行爬虫和推送通知。")

    return True

if __name__ == '__main__':
    success = test_github_actions()
    sys.exit(0 if success else 1)
