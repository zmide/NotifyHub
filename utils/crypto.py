from cryptography.fernet import Fernet
import base64
from flask import current_app


class ConfigEncryptor:
    @staticmethod
    def get_cipher():
        # 从配置获取密钥并确保长度正确
        key = current_app.config['ENCRYPTION_KEY'].encode()
        # Fernet需要32字节的urlsafe base64编码密钥
        key = base64.urlsafe_b64encode(key.ljust(32, b'=')[:32])
        return Fernet(key)

    @staticmethod
    def encrypt_config(config_str):
        cipher = ConfigEncryptor.get_cipher()
        return cipher.encrypt(config_str.encode()).decode()

    @staticmethod
    def decrypt_config(encrypted_str):
        cipher = ConfigEncryptor.get_cipher()
        return cipher.decrypt(encrypted_str.encode()).decode()
