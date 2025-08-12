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

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip==23.0.1 && \
    python -m pip install --no-cache-dir -r requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --trusted-host pypi.tuna.tsinghua.edu.cn

COPY . .

RUN mkdir -p /var/lib/notifyhub

ENV FLASK_APP=app.py \
    FLASK_DEBUG=0 \
    DATABASE_URL=sqlite:////var/lib/notifyhub/database.db

EXPOSE 5000

CMD ["sh", "-c", "flask init-db && gunicorn --bind 0.0.0.0:5000 app:app"]

