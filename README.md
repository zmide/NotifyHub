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
├── Dockerfile            # Docker配置文件
├── docker-compose.yml    # Docker Compose模板
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

- ✅ 多通知渠道集成：支持SMTP邮件、阿里云短信、Telegram、钉钉、飞书、企业微信和webhook
- 🔑 用户认证系统：注册、登录、API Token管理
- 🚀 RESTful API：通过简单的API调用发送通知
- 🛠️ 通道管理：添加、编辑、删除通知通道
- 📱 响应式设计：适配各种设备屏幕

## 支持的渠道

| 渠道类型     | 图标 | 描述                 |
|----------|------|--------------------|
| SMTP邮件   | 📧 | 通过SMTP协议发送邮件 |
| 阿里云短信  | 📱 | 通过阿里云短信服务发送短信 |
| Telegram | ✈️ | 通过Telegram Bot发送消息 |
| 钉钉      | 💬 | 通过钉钉机器人发送消息 |
| 飞书      | 📝 | 通过飞书机器人发送消息 |
| 企业微信   | 🏢 | 通过企业微信机器人发送消息 |
| Webhook  | 🌐 | 通过Webhook发送消息 |

## 快速开始

### 推荐方式：使用Docker部署（生产环境推荐）

1. 构建Docker镜像：
```bash
docker build -t notifyhub .
```

2. 运行容器：

使用[docker-compose.yml](./docker-compose.yml)部署！
```bash
services:
  notifyhub:
    image: notifyhub
    ports:
      - "5000:5000"
    env_file:
      - .env
    volumes:
      - notifyhub-data:/var/lib/notifyhub
    depends_on:
      mysql:
        condition: service_healthy
    command: sh -c "sleep 5 && python app.py"  # 添加启动延迟
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    ports:
      - "3307:3306"
    environment:
      TZ: Asia/Shanghai
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: notifyhub
    volumes:
      - mysql-data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 5s
      timeout: 10s
      retries: 20
      start_period: 30s  # 给MySQL更长的初始化时间
    restart: unless-stopped

volumes:
  notifyhub-data:
  mysql-data:
```
配置文件详解

在 `.env` 文件中可以配置以下选项：
 
```env
# 基本配置
SECRET_KEY=your-secret-key # 可使用下方命令生成
ENCRYPTION_KEY=your-encryption-key-here # 可使用下方命令生成

# MySQL数据库配置
MYSQL_ROOT_PASSWORD=123456
DATABASE_URL=mysql+pymysql://root:123456@mysql/notifyhub

# 注册功能开关 (true/false)
REGISTRATION_ENABLED=true

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```
```bash
# 生成SECRET_KEY
python -c "import secrets; print( secrets.token_hex(32))"

# 生成ENCRYPTION_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
`SECRET_KEY`:Flask 安全密钥。</br>
`ENCRYPTION_KEY`:通道配置加密密钥。</br>
`MYSQL_ROOT_PASSWORD`:数据库ROOT密码（默认123456，建议设置复杂）。</br>
`DATABASE_URL`:数据库连接URL（密码与上面设置一样）。</br>
`REGISTRATION_ENABLED`:注册功能开关。</br>
`ENCRYPTION_KEY`:通道配置加密密钥。</br>
`REGISTRATION_ENABLED`:是否开启注册。</br>



3. 访问应用：
```
http://localhost:5000
```

### 本地运行（开发环境）

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 配置选项
在 `.env` 文件中可以配置以下选项：
 
```env
# 基本配置
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key-here

# MySQL数据库配置
MYSQL_ROOT_PASSWORD=123456
DATABASE_URL=mysql+pymysql://root:123456@localhost/notifyhub

# 注册功能开关 (true/false)
REGISTRATION_ENABLED=true

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

#### 配置环境变量

1. 复制`.env.template`文件为`.env`文件：
```bash
cp .env.template .env
```

2. 生成安全密钥（自动追加到.env文件）：
```bash
# 生成SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

# 生成ENCRYPTION_KEY
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env
```

#### 运行应用
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