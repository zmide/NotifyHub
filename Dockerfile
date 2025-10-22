FROM python:3.8-slim

RUN echo > /etc/apt/sources.list.d/debian.sources && \
    echo "Types: deb" >> /etc/apt/sources.list.d/debian.sources && \
    echo "URIs: https://mirrors.tuna.tsinghua.edu.cn/debian" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Suites: bookworm bookworm-updates bookworm-backports" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Components: main contrib non-free non-free-firmware" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg" >> /etc/apt/sources.list.d/debian.sources && \
    echo >> /etc/apt/sources.list.d/debian.sources && \
    echo "Types: deb" >> /etc/apt/sources.list.d/debian.sources && \
    echo "URIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Suites: bookworm-security" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Components: main contrib non-free non-free-firmware" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg" >> /etc/apt/sources.list.d/debian.sources

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r notifyhub && useradd -r -g notifyhub notifyhub

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip==23.0.1 && \
    python -m pip install --no-cache-dir -r requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --trusted-host pypi.tuna.tsinghua.edu.cn

COPY . .

# 创建数据目录并设置权限
RUN mkdir -p /app/data && \
    chown -R notifyhub:notifyhub /app

# 获取用户ID用于权限设置
RUN id notifyhub

ENV FLASK_APP=app.py \
    FLASK_DEBUG=0

EXPOSE 5000

# 创建启动脚本
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "=== 启动脚本开始 ==="\n\
echo "当前用户: $(whoami)"\n\
echo "当前目录: $(pwd)"\n\
\n\
# 确保数据目录存在并有正确权限\n\
echo "创建数据目录..."\n\
mkdir -p /app/data\n\
\n\
echo "设置目录权限..."\n\
chown -R notifyhub:notifyhub /app/data\n\
chmod -R 755 /app/data\n\
\n\
echo "检查目录权限:"\n\
ls -la /app/data\n\
\n\
echo "检查环境变量:"\n\
echo "DATABASE_URL: $DATABASE_URL"\n\
\n\
# 测试数据库文件创建\n\
echo "测试数据库文件创建权限..."\n\
su notifyhub -c "touch /app/data/test.db && rm /app/data/test.db"\n\
echo "数据库文件创建权限正常"\n\
\n\
echo "切换到notifyhub用户并启动应用..."\n\
su notifyhub -c "cd /app && flask init-db && gunicorn --bind 0.0.0.0:5000 app:app"\n\
' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
