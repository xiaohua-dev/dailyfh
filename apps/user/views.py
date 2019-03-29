from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from user.models import User, Address
from django.views.generic import View
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
# 认证模块
from django.contrib.auth import authenticate, login, logout # logout 退出清除
from utils.mixin import LoginRequiredMixin #访问页面之前登录验证接口
import re

# Create your views here.

def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
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
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {"errmsg": "用户已存在"})

        user = User.objects.create_user(username, pwd, email)

        return redirect(reverse('goods:index'))

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
    except User.DoesNotExist:
        user = None

    if user:
        return render(request, 'register.html', {"errmsg": "用户已存在"})

    user = User.objects.create_user(username, pwd, email)

    return redirect(reverse('goods:index'))

class RegisterView(View):
    '''注册'''
    def get(self, request):
        return render(request, 'register.html')

    """注册助理"""
    def post(self, request):
        # 获取客户端传入注册信息
        username = request.POST.get("user_name")
        pwd = request.POST.get("pwd")
        email = request.POST.get("email")
        print(email)
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
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {"errmsg": "用户已存在"})

        user = User.objects.create_user(username, email, pwd)
        user.is_active = 0
        user.save()

        # 发送激活的邮件，包含激活链接：http://x.x.x.x:port/user/active/3
        # 激活链接中需要包含用户的身份信息，并且要把身份信息进行加密

        # 加密用户的身份信息，生产激活token
        serializer = Serializer(settings.SECRET_KEY,3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode('utf-8')

        # 发出异步执行的函数
        send_register_active_email.delay(email, username, token)

        return redirect(reverse('goods:index'))

class ActiveView(View):
    def get(self, request, token):
        """用户激活"""
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 获取用户id
            info = serializer.loads(token)

            # 获取用户信息
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as sig:
            # 实际项目中应该让其点击发送激活邮件
            return HttpResponse("激活链接过去")

class LoginView(View):
    """登录"""
    def get(self, request):
        #return render(request, 'login.html')
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})


    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("pwd")

        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})


        user = authenticate(username=username,password=password)

        if user is not None:
            if user.is_active:
                # 用户已激活
                # 记录用户登录状态
                login(request, user)

                # 登录之后页面跳转，重要******；获取未登录时访问的页面
                next_url = request.GET.get('next', reverse('goods:index'))
                response = redirect(next_url)

                remember = request.POST.get('remember')
                print(remember)

                if remember == 'on':
                    response.set_cookie('username',username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活，请激活'})
        else:
            return render(request, 'login.html', {'errmsg': '账号或密码错误'})

class LogoutView(LoginRequiredMixin,View):
    def get(self,requst):
        '''退出登录'''
        # 清除session信息
        logout(requst)

        return redirect(reverse('goods:index'))

class UserInfoView(View):
    def get(self,request):
        # page='user'
        # request.user
        # 如果用户未登录-> AnonymouseUser类的实例
        # 如果用户登录-> User类的一个实例
        # request.user.is_authenticated（）

        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request, 'user_center_info.html', {'page':'user'})

class UserOrderView(LoginRequiredMixin, View):
    def get(self,request):
        return render(request, 'user_center_order.html', {'page':'order'})

#class UserSiteView(LoginRequiredMixin, View):
#    def get(self,request):
#        return render(request, 'user_center_site.html', {'page':'address'})



class AddressView(LoginRequiredMixin,View):
    def get(self,request):
        user = request.user

        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None

        return render(request, 'user_center_site.html', {'page': 'address','address': address})

    def post(self,request):
        recevier = request.POST.get('recevier')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        if not all([recevier, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

        user = request.user

        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None

        if address:
            is_default = False
        else:
            is_default = True


        Address.objects.create(
            user=user,
            receiver=recevier,
            addr = addr,
            zip_code = zip_code,
            phone = phone,
            is_default=is_default
        )

        return redirect(reverse('user:address'))





