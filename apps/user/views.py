from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from user.models import User
import re

# Create your views here.

def register(request):
    return render(request, 'register.html')

def register_handle(request):
    # 获取客户端传入注册信息
    username = request.POST.get("user_name")
    pwd = request.POST.get("pwd")
    email = request.POST.get("email")
    cpwd = request.POST.get("cpwd")
    allow = request.POST.get("allow")

    # 注册信息校验
    if not all([username, pwd, email]):
        return render(request, 'register', {'errmsg': "数据不完整"})

    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register', {'errmsg': "邮箱格式不正确"})

    if allow != 'on':
        return render(request, 'register', {'errmsg': "请同意协议"})

    if pwd != cpwd:
        return render(request, 'register', {'errmsg': "两次输入的密码不一致"})

    # 用户注册
    try:
        user = User.objects.get(username=username)
    except User.DoseNotExits:
        user = None

    if user:
        return  render(request, 'register.html', {"errmsg": "用户已存在"})

    user = User.objects.create_user(username, pwd, email)

    return redirect(reverse('goods:index'))
