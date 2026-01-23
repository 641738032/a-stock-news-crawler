# 快速开始指南

## 本地测试

### 1. 安装依赖
```bash
cd /Users/zhuxl/Desktop/projects/a-stock-news-crawler
pip install -r requirements.txt
```

### 2. 运行爬虫
```bash
python src/main.py
```

### 3. 查看日志
```bash
tail -f logs/crawler_*.log
```

### 4. 查看爬取的数据
```bash
cat data/财联社_news.json
cat data/雪球_news.json
```

## GitHub 部署步骤

### 1. 创建 GitHub 仓库
```bash
# 在 GitHub 上创建新仓库 a-stock-news-crawler

# 添加远程仓库
git remote add origin https://github.com/yourusername/a-stock-news-crawler.git
git branch -M main
git push -u origin main
```

### 2. 配置 Secrets

在 GitHub 仓库设置中添加以下 Secrets:

**企业微信推送** (可选):
- `WECHAT_WEBHOOK_URL`: 你的企业微信 webhook URL

**邮箱推送** (可选):
- `EMAIL_SMTP_HOST`: SMTP 服务器 (如: smtp.qq.com)
- `EMAIL_SMTP_PORT`: SMTP 端口 (如: 587)
- `EMAIL_USER`: 发件人邮箱
- `EMAIL_PASSWORD`: 邮箱授权码
- `EMAIL_RECIPIENTS`: 收件人邮箱 (多个用逗号分隔)

### 3. 启用 GitHub Actions

在 Actions 标签页中启用工作流。

### 4. 手动触发测试

在 Actions 标签页中，选择 "A股新闻爬虫定时任务" 工作流，点击 "Run workflow" 手动触发。

## 配置说明

### 本地配置

1. 复制配置示例:
```bash
cp config/config.example.yaml config/config.yaml
```

2. 编辑 `config/config.yaml` 根据需要修改

3. 设置环境变量 (可选):
```bash
export WECHAT_WEBHOOK_URL="your-webhook-url"
export EMAIL_SMTP_HOST="smtp.qq.com"
export EMAIL_SMTP_PORT="587"
export EMAIL_USER="your-email@qq.com"
export EMAIL_PASSWORD="your-auth-code"
export EMAIL_RECIPIENTS="recipient@example.com"
```

## 常见问题

### Q: 爬虫无法获取数据？

A: 检查以下内容:
1. 网络连接是否正常
2. 目标网站是否可访问
3. 查看日志文件了解详细错误

### Q: 推送失败？

A: 检查以下内容:
1. 环境变量是否正确配置
2. 企业微信 webhook URL 是否有效
3. 邮箱 SMTP 配置是否正确

### Q: 如何修改爬取频率？

A: 编辑 `.github/workflows/crawler.yml` 中的 cron 表达式

## 项目位置

```
/Users/zhuxl/Desktop/projects/a-stock-news-crawler/
```

## 下一步

1. 在 GitHub 上创建仓库并推送代码
2. 配置 Secrets
3. 启用 GitHub Actions
4. 等待定时任务自动运行

祝使用愉快！
