# 统一通知平台

一个基于Flask的Web应用，集成了多种通知渠道（邮件、短信、Telegram、钉钉、飞书等）的统一通知平台。

## WIKI
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/zmide/NotifyHub)

## 环境

本项目基于 Python 3.8 开发

## 项目结构

```
.
├── app.py                # 主应用文件
├── config.py             # 配置文件
├── .env.template         # 环境变量模板文件
├── requirements.txt      # 依赖文件
├── static/               # 静态文件
├── utils/                # 工具
│   └── crypto.py         # 加密工具
└── templates/            # 模板文件
    ├── base.html         # 基础模板
    ├── dashboard.html    # 控制台页面
    ├── edit_channel.html # 编辑通道页面
    ├── index.html        # 首页
    ├── login.html        # 登录页面
    ├── register.html     # 注册页面
    └── settings.html     # 设置页面
```

## 功能特性

- ✅ 多通知渠道集成：支持SMTP邮件、阿里云短信、Telegram、钉钉和飞书
- 🔑 用户认证系统：注册、登录、API Token管理
- 🚀 RESTful API：通过简单的API调用发送通知
- 🛠️ 通道管理：添加、编辑、删除通知通道
- 📱 响应式设计：适配各种设备屏幕

## 支持的渠道

| 渠道类型 | 图标 | 描述 |
|----------|------|------|
| SMTP邮件 | <i class="bi bi-envelope"></i> | 通过SMTP协议发送邮件 |
| 阿里云短信 | <i class="bi bi-phone"></i> | 通过阿里云短信服务发送短信 |
| Telegram | <i class="bi bi-telegram"></i> | 通过Telegram Bot发送消息 |
| 钉钉 | <i class="bi bi-chat-dots"></i> | 通过钉钉机器人发送消息 |
| 飞书 | <i class="bi bi-chat-square-text"></i> | 通过飞书机器人发送消息 |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```
## 配置选项
 
在 `.env` 文件中可以配置以下选项：
 
```env
# 基本配置
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///database.db

# 加密配置（必须！用于加密通道敏感信息）
ENCRYPTION_KEY=your-encryption-key-here

# 注册功能开关 (true/false)
REGISTRATION_ENABLED=true
 
# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=5000

```

### 配置环境变量

1. 复制`.env.template`文件为`.env`文件：
```bash
cp .env.template .env
```

2. 生成安全密钥（自动追加到.env文件）：
```bash
# 生成SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

# 生成ENCRYPTION_KEY（必须！用于加密敏感配置）
echo "ENCRYPTION_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env

```

### 运行应用

```bash
python app.py
```

应用启动后，访问 http://127.0.0.1:5000 即可使用

## API使用示例

```bash
见项目控制台
```

## 安全说明

🔐 **重要安全提示**：
1. `ENCRYPTION_KEY` 是加密通道配置的关键密钥
2. 密钥一旦丢失，已加密的数据将无法解密
3. 生产环境建议：
   - 使用密钥管理服务（如AWS KMS、HashiCorp Vault）
   - 不要将`.env`文件提交到版本控制



## Telegram 通知通道配置指南

### 获取 Telegram Bot Token

国内无法直连TG API请提前准备代理！！！

代理可在通道配置中添加！！！

1. **创建 Telegram Bot**:
   - 在 Telegram 中搜索并联系 `@BotFather`
   - 发送 `/newbot` 命令
   - 按照提示输入机器人名称和用户名（必须以 `bot` 结尾）
   - 创建成功后，`@BotFather` 会提供你的 Bot Token，格式为 `数字:字母数字组合`

2. **获取 Chat ID**:
   - **个人聊天**: 
     - 给你的机器人发送任意消息
     - 访问 `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
     - 在返回的 JSON 中查找 `chat.id` 字段

   - **群组聊天**:
     - 将机器人添加到群组
     - 在群组中发送任意消息
     - 同样通过 `getUpdates` 接口获取群组的 `chat.id`

## 联系我们
admin@jrboy.cn

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

[MIT license](./LICENSE).