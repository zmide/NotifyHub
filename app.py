
import secrets
import base64
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from config import Config
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
import json
import idna
import hmac
import hashlib
import time
import urllib.parse

# 初始化应用
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    token = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    channels = db.relationship('NotificationChannel', backref='user', lazy=True)


class NotificationChannel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    channel_id = db.Column(db.String(80), nullable=False)
    channel_type = db.Column(db.String(20), nullable=False)
    config = db.Column(db.Text, nullable=False)  # 存储为JSON字符串
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_decrypted_config(self):
        """获取解密后的配置"""
        from utils.crypto import ConfigEncryptor
        try:
            return json.loads(ConfigEncryptor.decrypt_config(self.config))
        except:
            # 兼容未加密的旧数据
            return json.loads(self.config)

    def set_encrypted_config(self, config_dict):
        """加密并存储配置"""
        from utils.crypto import ConfigEncryptor
        self.config = ConfigEncryptor.encrypt_config(json.dumps(config_dict))



# 表单
class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被使用')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该邮箱已被注册')


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')


class ChannelForm(FlaskForm):
    channel_id = StringField('通道ID', validators=[DataRequired(), Length(min=2, max=50)])
    channel_type = SelectField('通道类型', choices=[
        ('smtp', 'SMTP邮件'),
        ('sms', '阿里云短信'),
        ('tg', 'Telegram'),
        ('dingtalk', '钉钉'),
        ('feishu', '飞书'),
        ('wechat', '企业微信'),
        ('webhook', 'webhook')
    ], validators=[DataRequired()])
    config = TextAreaField('配置(JSON格式)', validators=[DataRequired()])
    submit = SubmitField('保存')

    def validate_config(self, config):
        try:
            json.loads(config.data)
        except ValueError:
            raise ValidationError('配置必须是有效的JSON格式')


# 登录管理器
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/refresh_token', methods=['POST'])
@login_required
def refresh_token():
    # 生成新的token
    current_user.token = secrets.token_hex(32)
    db.session.commit()
    return jsonify({'status': 'success', 'new_token': current_user.token})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if not app.config['REGISTRATION_ENABLED']:
        flash('当前系统已关闭注册功能', 'danger')
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        token = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),  # 使用哈希加密
            token=token
        )
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录。', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('用户名或密码错误', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = ChannelForm()
    if form.validate_on_submit():
        existing = NotificationChannel.query.filter_by(
            user_id=current_user.id,
            channel_id=form.channel_id.data
        ).first()
        if existing:
            flash('通道ID已存在，请使用其他ID', 'danger')
        else:
            channel = NotificationChannel(
                user_id=current_user.id,
                channel_id=form.channel_id.data,
                channel_type=form.channel_type.data
            )
            channel.set_encrypted_config(json.loads(form.config.data))  # 使用加密方法
            db.session.add(channel)
            db.session.commit()
            flash('通道配置已保存', 'success')
            return redirect(url_for('dashboard'))
    return render_template('settings.html', form=form)


@app.route('/settings/edit/<int:channel_id>', methods=['GET', 'POST'])
@login_required
def edit_channel(channel_id):
    # 获取通道对象
    channel = NotificationChannel.query.get_or_404(channel_id)

    # 权限检查
    if channel.user_id != current_user.id:
        flash('无权访问该通道', 'danger')
        return redirect(url_for('settings'))

    form = ChannelForm()

    # POST请求处理（提交表单时）
    if form.validate_on_submit():
        # 检查通道ID是否已存在
        existing = NotificationChannel.query.filter(
            NotificationChannel.user_id == current_user.id,
            NotificationChannel.channel_id == form.channel_id.data,
            NotificationChannel.id != channel.id
        ).first()

        if existing:
            flash('通道ID已存在，请使用其他ID', 'danger')
        else:
            channel.channel_id = form.channel_id.data
            channel.channel_type = form.channel_type.data
            try:
                # 将JSON字符串转为字典，然后加密存储
                config_dict = json.loads(form.config.data)
                channel.set_encrypted_config(config_dict)
            except json.JSONDecodeError:
                flash('配置必须是有效的JSON格式', 'danger')
                return redirect(url_for('edit_channel', channel_id=channel.id))

            db.session.commit()
            flash('通道配置已更新', 'success')
            return redirect(url_for('dashboard'))

    # GET请求处理（显示编辑表单时）
    if request.method == 'GET':
        form.channel_id.data = channel.channel_id
        form.channel_type.data = channel.channel_type
        try:
            decrypted_config = channel.get_decrypted_config()
            form.config.data = json.dumps(decrypted_config, indent=2)  # 美化JSON格式
        except:
            # 如果解密失败（如旧数据未加密），直接显示原始数据
            form.config.data = channel.config

    return render_template('edit_channel.html', form=form, channel=channel)


@app.route('/settings/delete/<int:channel_id>', methods=['POST'])
@login_required
def delete_channel(channel_id):
    channel = NotificationChannel.query.get_or_404(channel_id)
    if channel.user_id != current_user.id:
        flash('无权删除该通道', 'danger')
        return redirect(url_for('settings'))

    db.session.delete(channel)
    db.session.commit()
    flash('通道已删除', 'success')
    return redirect(url_for('dashboard'))


@app.route('/api/notify', methods=['POST'])
def notify():
    data = request.get_json()
    if not data or 'token' not in data or 'id' not in data or 'content' not in data:
        return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400

    user = User.query.filter_by(token=data['token']).first()
    if not user:
        return jsonify({'status': 'error', 'message': '无效token'}), 401

    channel = NotificationChannel.query.filter_by(
        user_id=user.id,
        channel_id=data['id']
    ).first()
    if not channel:
        return jsonify({'status': 'error', 'message': '通道ID不存在'}), 404

    try:
        # 使用解密后的配置
        config = channel.get_decrypted_config()
        result = None

        if channel.channel_type == 'smtp':
            result = send_email(config, data['content'])
        elif channel.channel_type == 'sms':
            result = send_sms(config, data['content'])
        elif channel.channel_type == 'tg':
            result = send_telegram(config, data['content'])
        elif channel.channel_type == 'dingtalk':
            result = send_dingtalk(config, data['content'])
        elif channel.channel_type == 'feishu':
            result = send_feishu(config, data['content'])
        elif channel.channel_type == 'wechat':
            result = send_wechat(config, data['content'])
        elif channel.channel_type == 'webhook':
            result = send_webhook(config, data['content'])
        else:
            return jsonify({'status': 'error', 'message': '不支持的通道类型'}), 400

        return jsonify({'status': 'success', 'message': '通知已发送'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_email(config, content):
    """发送邮件通知（支持国际化地址和完整发件人格式）"""
    try:
        # 1. 内容解析与校验
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = {"text_body": content}

        required_fields = ['to_email', 'subject', 'text_body']
        for field in required_fields:
            if field not in content:
                raise ValueError(f"缺少必要字段: {field}")

        # 2. 构建邮件头（国际化兼容处理）
        def format_email_address(display_name, email_address):
            """标准化邮箱地址格式"""
            try:
                # 处理国际化域名（如 公司.中国 -> xn--fiq228c.xn--fiqs8s）
                local_part, domain = email_address.split('@')
                domain_ascii = idna.encode(domain).decode('ascii')
                email_ascii = f"{local_part}@{domain_ascii}"

                # 返回格式化后的地址
                if display_name:
                    return formataddr((display_name, email_ascii))
                return email_ascii
            except Exception as e:
                raise ValueError(f"邮箱地址格式错误: {str(e)}")

        # 3. 构建邮件消息
        msg = MIMEText(content['text_body'], 'html', 'utf-8')
        msg['Subject'] = content['subject']

        # 发件人处理（显示名 + 配置中的邮箱）
        from_name = content.get('from_name', '').strip()
        msg['From'] = format_email_address(
            from_name,
            config['smtp_username']
        )

        # 收件人处理（支持多个收件人，用逗号分隔）
        to_emails = [e.strip() for e in content['to_email'].split(',')]
        msg['To'] = ', '.join(
            format_email_address(None, email) for email in to_emails
        )

        # 4. 邮件服务器连接（自动选择加密方式）
        port = config.get('smtp_port', 465)
        if config.get('use_ssl') or port == 465:
            server = smtplib.SMTP_SSL(config['smtp_server'], port, timeout=10)
        else:
            server = smtplib.SMTP(config['smtp_server'], port, timeout=10)
            try:
                server.starttls()
            except smtplib.SMTPNotSupportedError:
                pass

        # 5. 发送邮件
        server.login(config['smtp_username'], config['smtp_password'])
        server.send_message(msg)
        server.quit()
        return True

    except Exception as e:
        raise Exception(f"邮件发送失败: {str(e)}")


def send_sms(config, content):
    """发送阿里云短信通知（支持字典或JSON字符串输入）"""
    try:
        from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
        from alibabacloud_tea_util import models as util_models
        import json

        # 1. 检查config是否包含AK/SK
        if 'access_key_id' not in config or 'access_key_secret' not in config:
            raise ValueError("config必须包含access_key_id和access_key_secret")

        # 2. 处理content（支持字典或JSON字符串）
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError("content必须是字典或合法JSON字符串")
        if not isinstance(content, dict):
            raise ValueError("content必须是字典或JSON字符串")

        # 3. 检查必要参数
        required_fields = ['phone_numbers', 'sign_name', 'template_code']
        for field in required_fields:
            if field not in content:
                raise ValueError(f"content缺少必要参数: {field}")

        # 4. 创建配置
        api_config = open_api_models.Config(
            access_key_id=config['access_key_id'],
            access_key_secret=config['access_key_secret']
        )
        api_config.endpoint = 'dysmsapi.aliyuncs.com'

        # 5. 初始化客户端
        client = DysmsapiClient(api_config)

        # 6. 提取模板变量（排除系统参数）
        template_vars = {
            k: str(v) for k, v in content.items()
            if k not in required_fields
        }

        # 7. 构造请求参数
        send_sms_request = dysmsapi_models.SendSmsRequest(
            phone_numbers=content['phone_numbers'],
            sign_name=content['sign_name'],
            template_code=content['template_code'],
            template_param=json.dumps(template_vars, separators=(',', ':'))
        )

        # 8. 发送短信
        response = client.send_sms_with_options(
            send_sms_request,
            util_models.RuntimeOptions()
        )

        if response.body.code != 'OK':
            raise Exception(f"短信发送失败: {response.body.message}")
        return True

    except Exception as e:
        raise Exception(f"短信发送失败: {str(e)}")


def send_telegram(config, content):
    """发送Telegram通知"""
    try:
        # 确保api_url没有结尾斜杠
        api_url = config['api_url'].rstrip('/')
        url = f"{api_url}/bot{config['bot_token']}/sendMessage"

        payload = {
            'chat_id': config['chat_id'],
            'text': content,
            'parse_mode': 'HTML'
        }

        # 根据is_proxy决定是否使用代理
        proxies = None
        if config.get('is_proxy', False):
            if 'https_proxy' not in config:
                raise ValueError("启用代理但未配置https_proxy")
            proxies = {
                'https': config['https_proxy']
            }

        # 发送请求
        response = requests.post(
            url,
            data=payload,
            proxies=proxies,  # 自动处理None情况
            timeout=10
        )
        response.raise_for_status()

        # 检查Telegram返回的错误
        result = response.json()
        if not result.get('ok'):
            raise Exception(f"Telegram API错误: {result.get('description')}")

        return True
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        raise Exception(f"Telegram发送失败: {str(e)}")

def send_dingtalk(config, content):
    """发送钉钉通知（支持加签验证）"""
    try:
        webhook_url = config['webhook_url']
        secret = config.get('secret')

        if config.get('msg_type', 'text') == 'text':
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
        else:  # markdown
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": config.get('title', '通知'),
                    "text": content
                }
            }

        if config.get('at_mobiles'):
            payload["at"] = {
                "atMobiles": config['at_mobiles'],
                "isAtAll": False
            }

        if secret:
            timestamp = str(round(time.time() * 1000))
            sign = generate_sign(secret, timestamp)
            webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

        response = requests.post(webhook_url, json=payload)
        result = response.json()
        if result.get('errcode') != 0:
            raise Exception(f"钉钉发送失败: {result.get('errmsg')}")
        return True
    except Exception as e:
        raise Exception(f"钉钉发送失败: {str(e)}")
def generate_sign(secret, timestamp):
    """生成钉钉加签签名"""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return urllib.parse.quote_plus(base64.b64encode(hmac_code))


def send_feishu(config, content):
    """发送飞书通知"""
    try:
        webhook_url = config['webhook_url']

        payload = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }

        response = requests.post(webhook_url, json=payload)
        result = response.json()

        if result.get('code') != 0:
            raise Exception(f"飞书发送失败: {result.get('msg')}")
        return True
    except Exception as e:
        raise Exception(f"飞书发送失败: {str(e)}")

def send_wechat(config, content):
    """发送钉钉通知"""
    try:
        webhook_url = config['webhook_url']

        if config.get('msg_type', 'text') == 'text':
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
        else:  # markdown
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }

        response = requests.post(webhook_url, json=payload)
        result = response.json()

        if result.get('errcode') != 0:
            raise Exception(f"钉钉发送失败: {result.get('errmsg')}")
        return True
    except Exception as e:
        raise Exception(f"钉钉发送失败: {str(e)}")

def send_webhook(config, content):
    """发送webhook通知"""
    try:
        webhook_url = config['webhook_url']

        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            raise Exception(f"提交JSON格式错误")
        response = requests.post(webhook_url, json=payload)
        result = response.json()

        if result.get('errcode') != 0:
            raise Exception(f"webhook发送失败: {result.get('errmsg')}")
        return True

    except Exception as e:
        raise Exception(f"webhook发送失败: {str(e)}")



@app.context_processor
def inject_now():
    return {'now': datetime.now()}
# 初始化数据库
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(
        host=app.config['SERVER_HOST'],
        port=app.config['SERVER_PORT'],
        debug=True
    )
