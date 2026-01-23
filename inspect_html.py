#!/usr/bin/env python3
"""
检查网站 HTML 结构，找出正确的选择器
"""
import sys
import os
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def inspect_website(url, name):
    """检查网站 HTML 结构"""
    print(f"\n{'='*60}")
    print(f"检查 {name}: {url}")
    print(f"{'='*60}\n")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)  # 等待 JS 执行

            content = page.content()

            # 保存 HTML 到文件
            html_file = f"html_{name}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ HTML 已保存到: {html_file}\n")

            # 打印 HTML 片段（查找新闻相关的 div/article/li）
            print("寻找可能的新闻容器...\n")

            # 查找所有 div
            divs = page.query_selector_all('div[class*="item"]')
            print(f"找到 {len(divs)} 个包含 'item' 的 div")

            # 查找所有 article
            articles = page.query_selector_all('article')
            print(f"找到 {len(articles)} 个 article 标签")

            # 查找所有 li
            lis = page.query_selector_all('li')
            print(f"找到 {len(lis)} 个 li 标签")

            # 查找所有 class 包含 news/post/feed 的元素
            news_divs = page.query_selector_all('div[class*="news"]')
            print(f"找到 {len(news_divs)} 个包含 'news' 的 div")

            post_divs = page.query_selector_all('div[class*="post"]')
            print(f"找到 {len(post_divs)} 个包含 'post' 的 div")

            feed_divs = page.query_selector_all('div[class*="feed"]')
            print(f"找到 {len(feed_divs)} 个包含 'feed' 的 div")

            # 打印前几个元素的 HTML
            print("\n" + "="*60)
            print("前 5 个 li 元素的 HTML:")
            print("="*60 + "\n")

            for i, li in enumerate(lis[:5]):
                html = li.inner_html()
                print(f"--- LI #{i+1} ---")
                print(html[:300] + ("..." if len(html) > 300 else ""))
                print()

            browser.close()

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    inspect_website('https://www.cls.cn/telegraph', '财联社')
    inspect_website('https://xueqiu.com/hq', '雪球')
