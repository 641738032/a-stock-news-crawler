## 本地定时调度器使用指南

### 功能说明

`scheduler.py` 是一个本地定时任务调度器，提供以下功能：

1. **每个整点执行爬取** - 自动爬取财联社最新新闻并推送到邮箱和企业微信
2. **早上 8:30 发送总结** - 汇总前一天晚上 21:00 至今天早上 8:30 的所有新闻
3. **晚上 21:00 发送总结** - 汇总今天早上 8:30 至晚上 21:00 的所有新闻

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

在运行前，需要配置以下环境变量：

#### 邮箱配置
```bash
export EMAIL_SMTP_HOST="smtp.qq.com"           # SMTP 服务器地址
export EMAIL_SMTP_PORT="587"                   # SMTP 端口
export EMAIL_USER="your-email@qq.com"          # 发件人邮箱
export EMAIL_PASSWORD="your-auth-code"         # 邮箱授权码
export EMAIL_RECIPIENTS="recipient@qq.com"     # 收件人邮箱（多个用逗号分隔）
```

#### 企业微信配置
```bash
export WECHAT_WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
```

### 运行调度器

```bash
python scheduler.py
```

### 日志查看

日志文件保存在 `logs/` 目录下，按日期命名：
- `scheduler_YYYYMMDD.log` - 调度器日志
- `crawler_YYYYMMDD.log` - 爬虫日志

查看实时日志：
```bash
tail -f logs/scheduler_*.log
```

### 任务时间表

| 时间 | 任务 | 说明 |
|------|------|------|
| 每个整点 | 爬取并推送 | 爬取最新新闻，推送到邮箱和企业微信 |
| 08:30 | 早间总结 | 汇总前一天 21:00 至今天 08:30 的新闻 |
| 21:00 | 晚间总结 | 汇总今天 08:30 至晚上 21:00 的新闻 |

### 停止调度器

按 `Ctrl+C` 停止运行。

### 常见问题

#### 1. 邮件无法发送
- 检查环境变量是否正确配置
- 确认邮箱授权码是否正确（不是邮箱密码）
- 查看日志文件中的错误信息

#### 2. 企业微信无法推送
- 检查 webhook URL 是否正确
- 确认企业微信群机器人是否已启用
- 查看日志文件中的错误信息

#### 3. 新闻无法爬取
- 检查网络连接
- 查看日志文件中的错误信息
- 确认财联社网站是否可访问

### 后台运行

#### 使用 nohup（Linux/Mac）
```bash
nohup python scheduler.py > scheduler.log 2>&1 &
```

#### 使用 screen（Linux/Mac）
```bash
screen -S scheduler
python scheduler.py
# 按 Ctrl+A 然后 D 退出 screen
# 查看 screen: screen -ls
# 恢复 screen: screen -r scheduler
```

#### 使用 systemd（Linux）
创建 `/etc/systemd/system/stock-scheduler.service`：
```ini
[Unit]
Description=A Stock News Scheduler
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/a-stock-news-crawler
Environment="EMAIL_SMTP_HOST=smtp.qq.com"
Environment="EMAIL_SMTP_PORT=587"
Environment="EMAIL_USER=your-email@qq.com"
Environment="EMAIL_PASSWORD=your-auth-code"
Environment="EMAIL_RECIPIENTS=recipient@qq.com"
Environment="WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
ExecStart=/usr/bin/python3 /path/to/a-stock-news-crawler/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

然后运行：
```bash
sudo systemctl daemon-reload
sudo systemctl enable stock-scheduler
sudo systemctl start stock-scheduler
```

查看状态：
```bash
sudo systemctl status stock-scheduler
```

查看日志：
```bash
sudo journalctl -u stock-scheduler -f
```
