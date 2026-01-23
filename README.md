# A股新闻爬虫

一个自动化的 Python 爬虫项目，定时爬取财联社和雪球的A股相关新闻，并通过企业微信和邮箱推送新增内容。

## 功能特性

- 📰 **多数据源支持**: 财联社、雪球
- ⏰ **定时爬取**: 每小时自动执行
- 🔄 **增量检测**: 自动识别新增内容，避免重复推送
- 📢 **多通道推送**: 企业微信群机器人 + 邮箱
- 🕐 **交易时段控制**: 仅在工作日交易时段推送通知
- 📊 **数据持久化**: JSON 格式存储，版本控制友好
- ☁️ **云端部署**: 使用 GitHub Actions 免费定时运行
- 📝 **完整日志**: 详细的运行日志记录

## 项目结构

```
a-stock-news-crawler/
├── .github/
│   └── workflows/
│       └── crawler.yml              # GitHub Actions 工作流
├── src/
│   ├── scrapers/
│   │   ├── base.py                  # 爬虫基类
│   │   ├── cls_scraper.py           # 财联社爬虫
│   │   └── xueqiu_scraper.py        # 雪球爬虫
│   ├── notifiers/
│   │   ├── base.py                  # 推送基类
│   │   ├── wechat.py                # 企业微信推送
│   │   └── email.py                 # 邮箱推送
│   ├── utils/
│   │   ├── data_manager.py          # 数据管理
│   │   ├── time_utils.py            # 时间工具
│   │   └── logger.py                # 日志工具
│   └── main.py                      # 主程序
├── data/                            # 数据存储目录
├── logs/                            # 日志目录
├── config/
│   └── config.example.yaml          # 配置示例
├── requirements.txt                 # Python 依赖
├── .gitignore
└── README.md
```

## 快速开始

### 1. 本地开发

#### 克隆项目
```bash
git clone https://github.com/yourusername/a-stock-news-crawler.git
cd a-stock-news-crawler
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 运行爬虫
```bash
python src/main.py
```

### 2. GitHub Actions 部署

#### 步骤 1: Fork 项目到你的 GitHub 账户

#### 步骤 2: 配置 Secrets

在 GitHub 仓库设置中，添加以下 Secrets（Settings → Secrets and variables → Actions）：

**企业微信推送** (可选):
- `WECHAT_WEBHOOK_URL`: 企业微信群机器人 webhook URL

**邮箱推送** (可选):
- `EMAIL_SMTP_HOST`: SMTP 服务器地址 (如: smtp.qq.com)
- `EMAIL_SMTP_PORT`: SMTP 端口 (如: 587)
- `EMAIL_USER`: 发件人邮箱
- `EMAIL_PASSWORD`: 邮箱密码或授权码
- `EMAIL_RECIPIENTS`: 收件人邮箱 (多个用逗号分隔)

#### 步骤 3: 启用 GitHub Actions

在 Actions 标签页中启用工作流。

#### 步骤 4: 配置定时任务

工作流已配置为每小时执行一次。你也可以手动触发运行。

## 配置说明

### 配置文件 (config.yaml)

复制 `config/config.example.yaml` 为 `config/config.yaml`，根据需要修改：

```yaml
scrapers:
  cls:
    enabled: true          # 是否启用财联社爬虫
  xueqiu:
    enabled: true          # 是否启用雪球爬虫

notifiers:
  wechat:
    enabled: false         # 是否启用企业微信推送
  email:
    enabled: false         # 是否启用邮箱推送

schedule:
  trading_hours_only: true # 仅在交易时段推送
```

### 环境变量

所有敏感信息都应该通过环境变量配置：

```bash
export WECHAT_WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
export EMAIL_SMTP_HOST="smtp.qq.com"
export EMAIL_SMTP_PORT="587"
export EMAIL_USER="your-email@qq.com"
export EMAIL_PASSWORD="your-auth-code"
export EMAIL_RECIPIENTS="recipient1@example.com,recipient2@example.com"
```

## 推送配置

### 企业微信群机器人

1. 在企业微信中创建群组
2. 添加群机器人，获取 webhook URL
3. 将 webhook URL 配置到 `WECHAT_WEBHOOK_URL` 环境变量

### 邮箱推送

支持任何支持 SMTP 的邮箱服务：

**QQ 邮箱**:
- SMTP 服务器: smtp.qq.com
- 端口: 587
- 密码: 使用授权码 (在 QQ 邮箱设置中生成)

**163 邮箱**:
- SMTP 服务器: smtp.163.com
- 端口: 587
- 密码: 使用授权码

**Gmail**:
- SMTP 服务器: smtp.gmail.com
- 端口: 587
- 密码: 使用应用专用密码

## 数据格式

爬虫保存的新闻数据格式：

```json
{
  "id": "财联社_20260123103000_12345",
  "title": "新闻标题",
  "content": "新闻内容或摘要",
  "url": "https://example.com/news/123",
  "publish_time": "2026-01-23T10:30:00",
  "source": "财联社",
  "scraped_at": "2026-01-23T10:35:00",
  "extra": {
    "raw_time": "10:30",
    "likes": "100"
  }
}
```

## 交易时段

- **工作日**: 周一至周五
- **上午交易**: 09:30 - 11:30
- **下午交易**: 13:00 - 15:00
- **推送时机**: 仅在交易时段内有新增内容时推送

## 日志

日志文件保存在 `logs/` 目录，按日期命名：

```
logs/
├── crawler_20260123.log
├── crawler_20260124.log
└── ...
```

## 常见问题

### Q: 爬虫无法获取数据？

A: 可能原因：
1. 网络连接问题
2. 目标网站反爬虫限制
3. 网站结构变化

检查日志文件了解详细错误信息。

### Q: 推送失败？

A: 检查以下内容：
1. 环境变量是否正确配置
2. 企业微信 webhook URL 是否有效
3. 邮箱 SMTP 配置是否正确
4. 网络连接是否正常

### Q: 如何修改爬取频率？

A: 编辑 `.github/workflows/crawler.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 * * * *'  # 每小时
  # - cron: '*/30 * * * *'  # 每 30 分钟
  # - cron: '0 9-15 * * 1-5'  # 工作日 9-15 点每小时
```

### Q: 如何添加新的数据源？

A:
1. 在 `src/scrapers/` 中创建新的爬虫类，继承 `BaseScraper`
2. 实现 `scrape()` 方法
3. 在 `src/main.py` 中注册新爬虫
4. 在配置文件中启用新爬虫

## 技术栈

- **Python 3.11+**
- **requests**: HTTP 请求库
- **BeautifulSoup4**: HTML 解析
- **pandas**: 数据处理
- **PyYAML**: 配置管理
- **GitHub Actions**: 定时任务

## 注意事项

1. **遵守法律**: 爬虫应遵守网站的 robots.txt 和服务条款
2. **反爬虫**: 项目已实现请求重试、User-Agent 轮换等反爬虫措施
3. **隐私保护**: 不要将敏感信息（webhook URL、邮箱密码）提交到 git
4. **资源限制**: GitHub Actions 免费账户有使用时长限制
5. **中文编码**: 确保所有文件使用 UTF-8 编码

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交 Issue。

---

**最后更新**: 2026-01-23
