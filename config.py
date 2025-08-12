import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///database.db') # 开发环境
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:////var/lib/notifyhub/database.db') # 运行环境（linux）
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 添加加密密钥配置
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default-encryption_key')

    # IP及端口设置
    SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')
    SERVER_PORT = os.getenv('SERVER_PORT', '5000')

    # 注册功能开关
    REGISTRATION_ENABLED = os.getenv('REGISTRATION_ENABLED', 'true').lower() == 'true'