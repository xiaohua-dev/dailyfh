# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time

# django初始化环境
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()

# 创建一个celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://10.77.2.223:6379/8')

@app.task
def send_register_active_email(to_email, username, token):
    # 邮件发送
    subject = "欢迎登录商城"
    message = ""
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为本商城注册会员</h1>请点击下面的链接进行用户激活<br/><a href="http://10.77.2.223:9999/user/active/%s">http://10.77.2.223:9999/user/active/%s</a>' % (
    username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)
    time.sleep(2)