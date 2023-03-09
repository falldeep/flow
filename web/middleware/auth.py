import datetime

from  django.utils.deprecation import  MiddlewareMixin
from web  import models
from django.conf import settings
from django.shortcuts import redirect,HttpResponse

class Tracer:
    def __init__(self):
        self.user = None
        self.price_policy = None

class AuthMiddleware(MiddlewareMixin):

    def process_request(self,request):
        request.tracer = Tracer()
        user_id = request.session.get('user_id',0)
        user_object = models.UserInfo.objects.filter(id=user_id).first()
        request.tracer.user = user_object
        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return

        if not request.tracer.user:
            return redirect('web:login')

        """因为数据库存储了免费版的交易记录所以用这种方式，来判断用户为免费版用户还是付费版用户"""
        transaction = models.Transaction.objects.filter(user=user_object,status=2).order_by("-id").first()
        current_datetime = datetime.datetime.now()
        if transaction.end_datetime and transaction.end_datetime < current_datetime:
            transaction = models.Transaction.objects.filter(user=user_object,status=2,price_policy__category=1).first()
        request.tracer.price_policy = transaction.price_policy

        """如果免费版用户不在数据库存储，则可以通过以下方式来判断"""
        # transaction = transaction = models.Transaction.objects.filter(user=user_object,status=2).order_by("-id").first()
        # if not transaction:
        #     """免费版"""
        #     request.tracer.price_policy = models.PricePolicy.objects.filter(category=1,title="个人免费版").filter()
        # else:
        #     """付费版"""
        #     current_datetime = datetime.datetime.now()
        #     if transaction.end_datetime and transaction.end_datetime < current_datetime:
        #         request.tracer.price_policy = transaction.price_policy


    def process_view(self,request,func,args,kwagrs):

        if not request.path_info.startswith('/manage/'):
            return

        project_id = kwagrs.get('project_id')

        project_object = models.Project.objects.filter(id=project_id,creator=request.tracer.user).first()
        if project_object:
            request.tracer.project = project_object
            return

        project_user_object = models.ProjectUser.objects.filter(user=request.tracer.user,project=project_id).first()
        if project_user_object:
            request.tracer.project = project_user_object.project
            return
        return HttpResponse('无权限访问')
        # return redirect('web:project_list')
