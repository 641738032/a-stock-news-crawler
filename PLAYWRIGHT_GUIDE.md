# Playwright 安装和使用指南

## 快速开始

### 1. 安装依赖

```bash
# 安装 Python 包
pip install -r requirements.txt

# 安装 Playwright 浏览器驱动
playwright install chromium
```

### 2. 本地测试

```bash
# 运行调试脚本
python3 debug.py

# 或直接运行主程序
python3 src/main.py
```

### 3. GitHub Actions 自动配置

GitHub Actions 会自动安装 Playwright，无需额外配置。

## 工作原理

### 旧方案 (V1) - 仅 HTTP 请求
- ❌ 无法获取 JavaScript 动态加载的内容
- ✅ 速度快，资源消耗少

### 新方案 (V2) - Playwright 浏览器自动化
- ✅ 支持 JavaScript 动态渲染
- ✅ 模拟真实浏览器行为
- ✅ 更好的反爬虫兼容性
- ⚠️ 速度稍慢，资源消耗多

## 常见问题

### Q: Playwright 安装失败？

A: 确保您有足够的磁盘空间（约 500MB）。如果仍然失败，尝试：

```bash
# 清除缓存
rm -rf ~/.cache/ms-playwright

# 重新安装
playwright install chromium
```

### Q: 爬虫仍然无法获取数据？

A: 可能原因：
1. 网站结构变化 - 需要更新 CSS 选择器
2. 网站反爬虫限制 - 需要添加延迟或代理
3. 网站需要登录 - 需要添加认证

### Q: 如何加快爬取速度？

A: 可以尝试：
1. 减少 `wait_time` 参数
2. 使用并发爬虫
3. 缓存已爬取的数据

### Q: GitHub Actions 中 Playwright 会自动安装吗？

A: 是的，GitHub Actions 会自动安装 Playwright。如果需要手动配置，可以在 workflow 中添加：

```yaml
- name: Install Playwright
  run: |
    pip install playwright
    playwright install chromium
```

## 性能优化建议

### 1. 并发爬虫

如果需要同时爬取多个网站，可以使用 Python 的 `concurrent.futures`：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    cls_future = executor.submit(cls_scraper.scrape)
    xueqiu_future = executor.submit(xueqiu_scraper.scrape)

    cls_news = cls_future.result()
    xueqiu_news = xueqiu_future.result()
```

### 2. 缓存机制

避免重复爬取相同的页面：

```python
# 在 data_manager 中实现缓存
cache = {}
if url in cache:
    return cache[url]
```

### 3. 代理池

如果被限流，可以使用代理池：

```python
# 在 browser_base.py 中添加代理支持
proxy = random.choice(proxy_list)
context = browser.new_context(proxy=proxy)
```

## 故障排查

### 检查 Playwright 安装

```bash
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

### 查看详细日志

```bash
# 启用 Playwright 调试日志
export DEBUG=pw:api
python3 src/main.py
```

### 测试单个爬虫

```bash
python3 -c "
from src.scrapers.cls_scraper_v2 import CLSScraperV2
scraper = CLSScraperV2()
news = scraper.scrape()
print(f'爬取 {len(news)} 条新闻')
"
```

## 下一步

1. ✅ 安装 Playwright
2. ✅ 本地测试爬虫
3. ✅ 推送到 GitHub
4. ✅ 配置 GitHub Secrets
5. ✅ 启用 GitHub Actions

祝您使用愉快！
