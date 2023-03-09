#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
用户账户相关功能：注册、短信、登陆、注销
"""

from django.shortcuts import render,HttpResponse,redirect
from web.forms.account import RegisterModelFrom,SendSmsForm,LoginSmsForm,LoginForm
from django.http import JsonResponse
from django.db.models import Q
from web import models
from utils.img_code import check_code
from io import BytesIO
import uuid
import datetime

def register(request):
    if request.method == "GET":
       form = RegisterModelFrom()
       return render(request,'web/registers.html',{'form':form})

    form = RegisterModelFrom(data=request.POST)
    if form.is_valid():
        instance = form.save()
        policy_object = models.PricePolicy.objects.filter(category=1,title="个人免费版").first()
        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),
            user = instance,
            price_policy=policy_object,
            count=0,
            price=0,
            start_datetime=datetime.datetime.now(),
            end_datetime= datetime.datetime.now()+datetime.timedelta(days=365 * 100)
        )
        return JsonResponse({'status':True,"data":"/login"})
    else:
        return JsonResponse({'status':False,"error":form.errors})

def send_sms(request):
    "发送短信"
    form = SendSmsForm(request,data=request.GET)
    if form.is_valid():
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})

def login_sms(request):
   if request.method == "GET":
     form = LoginSmsForm(data=request.GET)
     return render(request,'web/login_sms.html',{'form':form})

   form = LoginSmsForm(data=request.POST)
   if form.is_valid():
       mobile_phone = form.cleaned_data['mobile_phone']
       user_object = models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()

       request.session['user_id']=user_object.id
       request.session.set_expiry(60 * 60 * 24 * 14)

       return JsonResponse({'status':True,"data":"home/"})
   return JsonResponse({'status':False,'error':form.errors})

def login(request):
    if request.method == "GET":
       form = LoginForm(request)
       return render(request,'web/login.html',{"form":form})

    form = LoginForm(request,data=request.POST)
    print(request.POST)
    print(form.is_valid())
    if form.is_valid():
        username  = form.cleaned_data['username']
        password = form.cleaned_data['password']
        print(username,1)
        user_object = models.UserInfo.objects.filter(Q(email = username) | Q(mobile_phone = username) |Q(username=username)).filter(password=password).first()

        if user_object:
            request.session['user_id'] = user_object.id
            request.session.set_expiry(60 * 60 * 24 * 14)
            return redirect('web:home')

        form.add_error('username','用户名或密码错误')
    return render(request,'web/login.html',{'form':form})


def img_code(request):
    """生成图片验证码"""

    img_object,code = check_code()

    request.session['image_code'] = code
    request.session.set_expiry(60)

    stream = BytesIO()
    img_object.save(stream,'png')

    return HttpResponse(stream.getvalue())

def logout(request):
    """退出登陆"""
    request.session.flush()
    return redirect('web:home')