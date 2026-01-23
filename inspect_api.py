#!/usr/bin/env python3
"""
高级诊断：检查网络请求和 API 调用
"""
import sys
import os
from playwright.sync_api import sync_playwright
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def inspect_api_calls(url, name):
    """检查网站的 API 调用"""
    print(f"\n{'='*60}")
    print(f"检查 {name} 的 API 调用: {url}")
    print(f"{'='*60}\n")

    api_calls = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 监听所有网络请求
            def handle_response(response):
                if 'api' in response.url or 'json' in response.url or response.url.endswith('.json'):
                    api_calls.append({
                        'url': response.url,
                        'status': response.status,
                        'method': response.request.method
                    })
                    print(f"API: {response.request.method} {response.url} -> {response.status}")

            page.on('response', handle_response)

            print(f"正在加载页面...")
            page.goto(url, wait_until='domcontentloaded', timeout=30000)

            print(f"等待 5 秒让 JS 执行...")
            page.wait_for_timeout(5000)

            print(f"\n检查页面内容...")
            content = page.content()

            # 查找 React/Vue 数据
            if '__NEXT_DATA__' in content:
                print("✓ 发现 Next.js 数据")
                start = content.find('__NEXT_DATA__')
                end = content.find('</script>', start)
                if start != -1 and end != -1:
                    data_str = content[start+13:end]
                    try:
                        # 提取 JSON
                        json_start = data_str.find('{')
                        json_end = data_str.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_str = data_str[json_start:json_end]
                            data = json.loads(json_str)
                            print(f"✓ 解析成功，数据大小: {len(json_str)} 字节")

                            # 查找新闻数据
                            def find_news_data(obj, depth=0):
                                if depth > 5:
                                    return
                                if isinstance(obj, dict):
                                    for k, v in obj.items():
                                        if 'news' in k.lower() or 'item' in k.lower() or 'list' in k.lower():
                                            print(f"  {'  '*depth}→ {k}: {type(v).__name__}")
                                            if isinstance(v, list) and len(v) > 0:
                                                print(f"    {'  '*depth}  (包含 {len(v)} 项)")
                                        find_news_data(v, depth+1)
                                elif isinstance(obj, list) and len(obj) > 0:
                                    find_news_data(obj[0], depth+1)

                            print("\n寻找新闻数据...")
                            find_news_data(data)
                    except Exception as e:
                        print(f"✗ JSON 解析失败: {e}")

            # 查找所有 script 标签中的数据
            scripts = page.query_selector_all('script')
            print(f"\n找到 {len(scripts)} 个 script 标签")

            # 查找页面中的实际内容
            print("\n查找页面中的文本内容...")
            text_content = page.inner_text('body')
            lines = [l.strip() for l in text_content.split('\n') if l.strip() and len(l.strip()) > 5]
            print(f"找到 {len(lines)} 行文本")
            print("前 10 行:")
            for line in lines[:10]:
                print(f"  {line[:80]}")

            browser.close()

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    inspect_api_calls('https://www.cls.cn/telegraph', '财联社')
    inspect_api_calls('https://xueqiu.com/hq', '雪球')
