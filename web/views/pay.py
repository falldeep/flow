import datetime
from django_redis import get_redis_connection
from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,redirect,reverse
from web import models
import json
from  utils.encrypt  import file_id
from utils.alipay import AliPay
from django.conf import settings


def price(request):
    """订单购买页面"""
    policy_list = models.PricePolicy.objects.filter(category=2)
    return render(request,'web/price.html',{'policy_list':policy_list})

def payment(request,policy_id):
    """支付页面"""
    policy_object = models.PricePolicy.objects.filter(id=policy_id,category=2).first()

    if not policy_object:
        return redirect('web:price')
    number = request.GET.get('number')
    if not number or not number.isdecimal():
        return redirect('web:price')
    number = int(number)
    if number < 1:
        return redirect('web:price')

    origin_price = number * policy_object.price

    balance = 0
    _object = None
    if request.tracer.price_policy.category == 2:
        _object = models.Transaction.objects.filter(user=request.tracer.user,status=2).order_by('-id').filter()
        total_time_delta= _object.end_datetime = _object.start_datetime
        balance_time_delta = _object.end_datetime - datetime.datetime.now()
        if total_time_delta.days == balance_time_delta.days:
            balance =  _object.price / total_time_delta.days * (balance_time_delta.days -1)
        else:
            balance = _object.price / total_time_delta.days * balance_time_delta.days
    if balance >= origin_price:
        return redirect('web:price')

    context = {
        'policy_id': policy_id,
        'number': number,
        'origin_price': origin_price,
        'balance': round(balance,2),
        'total_price': origin_price -round(balance,2),

    }

    conn = get_redis_connection()
    key = f'payment_{request.tracer.user.mobile_phone}'
    conn.set(key,json.dumps(context),ex=60 * 30)
    #原因是因为
    context['policy_object'] = policy_object
    context['transaction'] = _object

    return render(request,'web/payment.html',context)

def pays(request):
    conn = get_redis_connection()
    key = f'payment_{request.tracer.user.mobile_phone}'
    context_string = conn.get(key)

    if not context_string:
        return redirect('web:price')
    print(json.loads(context_string))
    context = json.loads(context_string.decode('utf-8'))

    order_id = file_id(request.tracer.user.mobile_phone)
    total_price = context['total_price']
    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.tracer.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=total_price,
    )

    #支付宝pay链接
    ali_pay = AliPay(
        appid=settings.PAY_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.PAY_PRI_KEY_PATH,
        alipay_public_key_path=settings.PAY_PUB_KEY_PATH,
    )

    query_params = ali_pay.direct_pay(
        subject="Tracer系统会员",
        out_trade_no=order_id,
        total_amount=total_price,
    )
    pay_url = f"{settings.PAY_GATEWAY}?{query_params}"
    return redirect(pay_url)


def pay_callback(request):
    """支付宝在支付成功之后会返回两个请求
    return_url 支付成功后以GET形式反馈订单信息给相关url
    app_notify_url 支付成功后以POST形式反馈订单信息给url
    因此两种请求return_url一般用户展示订单支付结果，app_notify_url用户更新状态
    """
    ali_pay = AliPay(
        appid=settings.PAY_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.PAY_PRI_KEY_PATH,
        alipay_public_key_path=settings.PAY_PUB_KEY_PATH,
    )

    if request.method == "GET":
        params= request.GET.dict()
        sign = params.pop('sgin',None)
        status = ali_pay.verify(params,sign)
        if status:
            return HttpResponse("支付完成")
        return HttpResponse("异常请求")

    else:
        from urllib.parse import parse_qs
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for k,v in post_data.items():
            post_dict[k]=v[0]
        sign = post_dict.pop('sign',None)
        status = ali_pay.verify(post_dict,sign)
        if status:
            current_datetime = datetime.datetime.now()
            out_trade_no = post_dict['out_trade_no']
            _object = models.Transaction.objects.filter(
                order=out_trade_no
            ).first()
            _object.status = 2
            _object.start_datetime = current_datetime
            _object.end_datetime = current_datetime+datetime.timedelta(days=365 * _object.count)
        return HttpResponse("POST请求返还")






