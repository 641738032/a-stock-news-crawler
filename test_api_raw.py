#!/usr/bin/env python3
"""
调试 API 响应内容
"""
import requests
import json

def test_cls_api():
    """测试财联社 API"""
    print("="*60)
    print("测试财联社 API")
    print("="*60)

    url = 'https://www.cls.cn/nodeapi/updateTelegraphList'
    params = {
        'app': 'CailianpressWeb',
        'hasFirstVipArticle': '0',
        'lastTime': '0',
        'os': 'web',
        'rn': '50',
        'subscribedColumnIds': '',
        'sv': '8.4.6',
        'sign': 'b397ff36b4640016fe5b07a29fa2d521'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")

        data = response.json()
        print(f"响应键: {list(data.keys())}")
        print(f"完整响应:\n{json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")

    except Exception as e:
        print(f"错误: {e}")

def test_xueqiu_api():
    """测试雪球 API"""
    print("\n" + "="*60)
    print("测试雪球 API")
    print("="*60)

    url = 'https://stock.xueqiu.com/v5/stock/hot_stock/list.json'
    params = {
        'page': '1',
        'size': '30',
        '_type': '10',
        'type': '10',
        'include': '1'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://xueqiu.com/hq',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"响应键: {list(data.keys())}")
            print(f"完整响应:\n{json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
        else:
            print(f"响应内容: {response.text[:500]}")

    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    test_cls_api()
    test_xueqiu_api()
