from django import forms
from web import models
import random
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from utils.sms import send_sms_single
from django_redis import get_redis_connection
from utils import encrypt
from web.forms.bootstrap import BootStrap


class RegisterModelFrom(forms.ModelForm):
    email = forms.CharField(label="邮箱",
                            max_length=32,
                            validators=[RegexValidator(r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{2,3}$','邮箱格式错误')],
                            error_messages={"required": "请输入邮箱"})

    mobile_phone = forms.CharField(label='手机号',
                                   validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'),],
                                   error_messages={"required":"请输入手机号"})

    password = forms.CharField(label='密码',
                               min_length=8,
                               max_length=16,
                               validators=[RegexValidator(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&])[A-Za-z\d$@$!%*?&]{8,10}',"密码要求最小长度8位，由数字、字符、字母大小写组成！")],
                               error_messages={'max_length': "密码不能大于16位","required": "请输入密码",
                                 },widget=forms.PasswordInput())

    confirm_password = forms.CharField(label='重复密码',widget=forms.PasswordInput(),error_messages={"required": "请再次输入密码",})
    verification_code = forms.CharField(label='验证码',error_messages={"required": "请输入短信验证码"})
    class Meta:
        model = models.UserInfo
        fields = ['username','email','password','confirm_password','mobile_phone','verification_code']

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name,field in self.fields.items():
            field.widget.attrs['class'] = "form-control"
            field.widget.attrs['placeholder'] = "请输入%s" % (field.label)

    def clean_username(self):
        username = self.cleaned_data['username'];

        if models.UserInfo.objects.filter(username=username).exists():
            raise  ValidationError("该用户名重复，已注册！")

        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if models.UserInfo.objects.filter(email=email).exists():
            raise  ValidationError("该邮箱以被已注册")
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        return encrypt.md5(password)

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = encrypt.md5(self.cleaned_data['confirm_password'])
        if password != confirm_password:
            raise  ValidationError('两次密码输入不一致')

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        if models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists():
            raise ValidationError('该手机号已被注册')
        return mobile_phone

    def clean_verification_code(self):
        verification_code = self.cleaned_data['verification_code']
        mobile_phone = self.cleaned_data.get('mobile_phone')

        if not mobile_phone:  # 手机号不存在，则验证码无需再校验，直接返回
            raise ValidationError('请输入手机号，在获取验证码')

        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone).decode('utf-8')

        if not redis_code:
            raise ValidationError('验证码失效，请重新发送！')

        if verification_code.strip() != redis_code:
            raise ValidationError('验证码输入错误！')


class SendSmsForm(forms.Form):
    mobile_phone = forms.CharField(label="手机号",validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'),])

    def __init__(self,request,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.request = request

    def clean_mobile_phone(self):
        "手机号校验钩子函数"
        mobile_phone = self.cleaned_data['mobile_phone']

        #判断短信模版
        tpl = self.request.GET.get('tpl')
        template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
        if not template_id:
            raise ValidationError('短信模版错误')

        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        #校验手机号是否注册
        if tpl == "login":
           if not exists:
               raise ValidationError('该手机号未注册，请先注册！')
        elif tpl == "register":
            if exists:
                raise ValidationError('该手机号已被注册！')

        #生成验证码 & 发送验证码
        code = random.randrange(1000,9999)
        sms = send_sms_single(mobile_phone, template_id, [code, ])
        if sms['result'] != 0:
            raise ValidationError('发送短信失败,{}'.format(sms))

        #验证码写入Redis
        conn = get_redis_connection()
        conn.set(mobile_phone,code,ex=60)

        return mobile_phone

class LoginSmsForm(BootStrap,forms.Form):
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    verification_code = forms.CharField(label='验证码')

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        exitis = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if not exitis:
            return ValidationError('手机号不存在')

        return mobile_phone

    def clean_verification_code(self):
        mobile_phone = self.cleaned_data.get('mobile_phone')
        verification_code = self.cleaned_data['verification_code']


        # if not mobile_phone:
        #     return verification_code
        exitis =  models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if not exitis:  # 手机号不存在，则验证码无需再校验，直接返回
            raise ValidationError('手机号码不存在，请先注册')

        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)

        if not redis_code:
            raise ValidationError('验证码失效或未发送，请重新发送！')

        redis_code = redis_code.decode('utf-8')

        if verification_code.strip() != redis_code:
            raise ValidationError('验证码输入错误！')

class LoginForm(BootStrap,forms.Form):
    username = forms.CharField(label="用户名")
    password = forms.CharField(label="密码",widget=forms.PasswordInput())
    verification_code = forms.CharField(label="图片验证码")

    def __init__(self,request,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.request = request

    def clean_password(self):
        password = self.cleaned_data['password']
        return encrypt.md5(password)

    def clean_verification_code(self):
        verification_code = self.cleaned_data['verification_code']
        session_code = self.request.session.get('image_code')
        if not session_code:
            raise ValidationError('验证码已过期，请重新输入！')

        if verification_code.strip().upper() != session_code.strip().upper():
            raise ValidationError('验证码输入错误！')

        return verification_code
