import datetime

from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,redirect,reverse
from web import models
from web.forms.issues import IssuesModelForm,IssuesReplyModelForm,InviteModelForm
from django.views.decorators.csrf import  csrf_exempt
from  utils.pagination import Pagination
from utils.encrypt import file_id
import json
from django.utils.safestring import mark_safe
import time

class CheckFilter:
    def __init__(self,name,data_list,request):
        self.data_list = data_list
        self.name = name
        self.request = request

    def __iter__(self):
        for item in self.data_list:
            key = str(item[0])
            value = item[1]
            ck = ""

            value_list = self.request.GET.getlist(self.name)
            if key in value_list:
                ck = "checked"
                value_list.remove(key)
            else:
                value_list.append(key)

            quety_dict = self.request.GET.copy()
            quety_dict._mutable = True
            quety_dict.setlist(self.name,value_list)

            if 'page' in quety_dict:
                quety_dict.pop('page')

            param_url = quety_dict.urlencode()
            if param_url:
                url = f"{self.request.path_info}?{param_url}"
            else:
                url = self.request.path_info

            html = f'<a class"cell" href="{url}"><input type="checkbox" {ck} /><label>{value}</label></a>'
            yield  mark_safe(html)

class SelectFilter:
    def __init__(self,name,data_list,request):
        self.name = name
        self.data_list = data_list
        self.request = request

    def __iter__(self):
        yield mark_safe('<select class="select2" multiple="multiple" style="width:100%;">')
        for item in self.data_list:
            key = str(item[0])
            value = item[1]
            selected = ""

            value_list = self.request.GET.getlist(self.name)
            if key in value_list:
                selected = 'selected'
                value_list.remove(key)
            else:
                value_list.append(key)

            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name,value_list)
            if 'page' in query_dict:
                query_dict.pop('page')

            param_url = query_dict.urlencode()
            if param_url:
                url = f"{self.request.path_info}?{param_url}"
            else:
                url = self.request.path_info

            html = f'<option value="{url}" {selected}>{value}</option>'
            yield mark_safe(html)
        yield mark_safe('</select>')


@csrf_exempt
def issues(request,project_id):
    if request.method == "GET":

        """筛选功能 通过get请求参数实现"""
        allow_filter_name = ['issues_type','status','priority','assign','attention']
        condicton = {}
        for name in allow_filter_name:
            value_list = request.GET.getlist(name)
            if not value_list:
                continue
            condicton["{}__in".format(name)] = value_list


        queryset = models.Issues.objects.filter(project_id=project_id).filter(**condicton)
        page_object = Pagination(
            current_page=request.GET.get('page'),
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET,
            per_page=8
        )
        issues_object_list = queryset[page_object.start:page_object.end]

        project_issues_type = models.IssuesType.objects.filter(project_id = project_id).values_list('id','title')

        project_total_user = [(request.tracer.project.creator_id,request.tracer.project.creator.username)]
        join_user = models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id','user__username')
        project_total_user.extend(join_user)



        filter_list = [
            {'title':'问题状态','filter':CheckFilter('issues_type',project_issues_type,request)},
            {'title':'状态','filter':CheckFilter('status',models.Issues.status_choices,request)},
            {'title': '优先级', 'filter': CheckFilter('priority', models.Issues.priority_choices, request), },
            {'title':'指派者','filter':SelectFilter('assign',project_total_user,request)},
            {'title': '关注者', 'filter': SelectFilter('attention', project_total_user, request)}
        ]

        forms = IssuesModelForm(request)

        invite_form = InviteModelForm()
        return render(request,'web/issues.html',{'forms':forms,'issues_object_list':
            issues_object_list,'page':page_object.page_html(),'filter_list':filter_list,'invite_form':invite_form})

    form = IssuesModelForm(request,data=request.POST)
    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.creator = request.tracer.user
        form.save()
        return JsonResponse({'status':True})
    return JsonResponse({'status':False,'error':form.errors})

def detail(request,project_id,issues_id):
    issues_object = models.Issues.objects.filter(id=issues_id).first()
    forms = IssuesModelForm(request,issues_id,instance=issues_object)
    return render(request,'web/issues_detail.html',{"forms":forms,"issues_id":issues_id})

@csrf_exempt
def record(request,project_id,issues_id):
    if request.method == "GET":
        reply_list = models.IssuesReply.objects.filter(issues_id=issues_id,issues__project=request.tracer.project)
        data_list = []
        for row in reply_list:
            data= {
                'id':row.id,
                'reply_type_text':row.get_reply_type_display(),
                'creator':row.creator.username,
                'datetime':row.create_datetime.strftime("%Y-%m-%d %H:%M"),
                'parent_id':row.reply_id,
                'content':row.content,
            }
            data_list.append(data)

        return JsonResponse({"status":True,'data':data_list})

    form = IssuesReplyModelForm(data=request.POST)
    if form.is_valid():
        form.instance.issues_id = issues_id
        form.instance.reply_type = 2
        form.instance.creator = request.tracer.user
        form.instance.project_id=project_id
        instance = form.save()

        info = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status':True,'data':info})
    return JsonResponse({'status':False,'error':form.errors})

@csrf_exempt
def change(request,project_id,issues_id):
    """前端发送正确数据格式
       {name:field,value:update_content}
    """
    issues_object = models.Issues.objects.filter(id=issues_id,project=project_id).first()
    post_dict = json.loads(request.body.decode('utf-8'))

    name = post_dict['name']
    value = post_dict['value']
    """获取字段"""
    field_object = models.Issues._meta.get_field(name)
    field_verbose = field_object.verbose_name


    """修改记录获取旧数据"""
    def old_issues_name(issues_field):
        if issues_field == "subject":
            old_issues = issues_object.subject
            return old_issues

        if issues_field == "issues_type":
            old_issues = issues_object.issues_type.title
            return old_issues

        if issues_field == "desc":
            old_issues = "内容发生了改变"
            return old_issues

        if issues_field == "status":
            old_issues = issues_object.get_status_display()
            return old_issues

        if issues_field == "priority":
            old_issues = issues_object.get_priority_display()
            return old_issues

        if issues_field == "assign":
            if  issues_object.assign is None:
                assign = "空"
                return assign
            assign = issues_object.assign.username
            return assign

        if issues_field == "attention":
            attention = issues_object.attention
            return attention

        if issues_field == "mode":
            mode = issues_object.get_mode_display()
            return mode

        if issues_field == "parent":
            if issues_object.parent is None:
               parent = "空"
               return parent
            parent = issues_object.parent.subject
            return parent

        if issues_field == "end_time":
            end_time = issues_object.end_time.strftime("%Y-%m-%d")
            return end_time




    def create_reply_record(content):
        """生成操作记录"""
        new_object = models.IssuesReply.objects.create(
            reply_type=1,
            issues=issues_object,
            content=change_record,
            creator=request.tracer.user,
            project_id=project_id,
        )

        new_reply_dice = {
            'id': new_object.id,
            'reply_type_text': new_object.get_reply_type_display(),
            'content':new_object.content,
            'creator': new_object.creator.username,
            'datetime': new_object.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id':new_object.reply_id
        }
        return new_reply_dice

    def setattr_null():
        issues_old_name = old_issues_name(name)
        setattr(issues_object, name, None)
        issues_object.save()
        change_record = "{}由\"{}\"更新为\"空\"".format(field_verbose, issues_old_name)
        return change_record

    def setattr_value(value,choices_value=None):
        issues_old_name = old_issues_name(name)
        setattr(issues_object, name, value)
        issues_object.save()
        change_record = "{}由\"{}\"更新为\"{}\"".format(field_verbose, issues_old_name, value)
        return change_record


    def update_value_json(change_record):
       json =  {'status': True, 'data': create_reply_record(change_record)}
       return json

    null_error_json = {'status':False,'error':"{} 不能为空必须填写内容".format(field_verbose)}
    not_exist_json = {'status':False,'error':"值不存在（你可能是来捣乱的！！！）"}
    data_format_error_json = {'status':False,'error':"非法数据格式"}

    text_field = ['subject','desc','start_time','end_time']
    fk_field = ['issues_type','moduls','parent','assign']
    choices_field = ['priority', 'status', 'mode']

    """文本字段验证"""
    if name in text_field:
        if not value:
            if not field_object.null:
                return JsonResponse(null_error_json)
            change_record = setattr_null()
        else:
            change_record = setattr_value(value)
        return JsonResponse(update_value_json(change_record))

    """FK字段验证"""
    if name in fk_field:
        if not value:
            if not field_object.null:
                return JsonResponse(null_error_json)
            change_record = setattr_null()
        else:
            if name == "assign":
                """判断assign是否为项目创建者或者参与者"""
                if value == str(request.tracer.project.creator_id):
                    instance = request.tracer.project.creator
                else:
                    project_user_object = models.ProjectUser.objects.filter(project_id=project_id,
                                                                            user_id=value)
                    if project_user_object:
                        instance = project_user_object.user
                    else:
                        instance = None
                if  instance is None:
                    return JsonResponse(not_exist_json)

                change_record = setattr_value(instance)

            else:
                instance = field_object.remote_field.model.objects.filter(id=value, project_id=project_id).first()
                if not instance:
                    return JsonResponse(not_exist_json)
                change_record = setattr_value(instance)
        return JsonResponse(update_value_json(change_record))

    """choices字段验证"""
    if name in choices_field:
        selected_text = None
        for key,text in field_object.choices:
            if str(key) == value:
                selected_text = key
        if not selected_text:
            return JsonResponse(not_exist_json)
        issues_old_name = old_issues_name(name)
        setattr(issues_object, name, value)
        issues_object.save()
        change_record = "{}由\"{}\"更新为\"{}\"".format(field_verbose, issues_old_name, text)
        return JsonResponse(update_value_json(change_record))

    if name == "attention":
        if not isinstance(value,list):
            return JsonResponse(data_format_error_json)
        if not value:
            issues_object.attention.set(value)
            issues_object.save()
            change_record = "{}更新为\"空\"".format(field_object.verbose_name)
            return JsonResponse(update_value_json(change_record))
        else:
            user_dict = {str(request.tracer.project.creator_id): request.tracer.project.creator.username}
            project_user_list = models.ProjectUser.objects.filter(project_id=project_id)
            for item in project_user_list:
                user_dict[str(item.user_id)] = item.user.username
            username_list = []
            for user_id in value:
                username =  user_dict.get(str(user_id))
                if not username:
                    return JsonResponse({'status':False,'error':'{}用户不存在'.format(username)})
                username_list.append(username)
            issues_object.attention.set(value)
            issues_object.save()
            change_record = f"{field_object.verbose_name}更新为了\"{username_list}\""
            return JsonResponse({'status': True, 'data': create_reply_record(change_record)})

    return JsonResponse(not_exist_json)


@csrf_exempt
def invite_url(request,project_id):
    """生成验证码"""
    form = InviteModelForm(data=request.POST)
    if form.is_valid():

        if request.tracer.user != request.tracer.project.creator:
            form.add_error("period","只有项目创建者才可以邀请成员！")
            return JsonResponse({'status':False,'error':form.errors})

        random_invite_code = file_id(request.tracer.user.mobile_phone)
        form.instance.project = request.tracer.project
        form.instance.code = random_invite_code
        form.instance.creator = request.tracer.user
        form.save()

        """验证码返回给前端"""
        url = "{scheme}://{host}{path}".format(
            scheme=request.scheme,
            host=request.get_host(),
            path=reverse('web:invite_join',kwargs={'code':random_invite_code})
        )
        return JsonResponse({'status':True,'data':url})

    return JsonResponse({'status':False,'error':form.errors})

@csrf_exempt
def invite_join(request,code):
    """访问邀请码"""
    invite_object = models.ProjectInvite.objects.filter(code=code).first()

    if not invite_object:
        return render(request,'web/invite_join.html',{'error':'邀请码不存在！'})

    if invite_object.project.creator == request.tracer.user:
        return render(request,'web/invite_join.html',{'error':'项目创建者无需加入此项目！'})


    exits = models.ProjectUser.objects.filter(project=invite_object.project,user=request.tracer.user).first()
    if exits:
       return render(request,'web/invite_join.html',{'error':'您已经是项目成员了，无需重复加入.'})

    max_tracsaction = models.Transaction.objects.filter(user=invite_object.project.creator).order_by('-id').first()
    current_datetime = datetime.datetime.now()
    if max_tracsaction.price_policy == 1:
        max_member = max_tracsaction.price_project.project_number
    else:
       if max_tracsaction.end_datetime < current_datetime:
          free_object = models.PricePolicy.objects.filter(category=1).first()
          max_member = free_object.project_member
       else:
           max_member = max_tracsaction.price_policy.project_member
    current_member = models.ProjectUser.objects.filter(project=invite_object.project).count()
    current_member +=1
    if current_member >= max_member:
        return render(request,'web/invite_join.html',{'error':'成员超出限制，，请升级套餐！'})
    limit_datetime = invite_object.create_datetime + datetime.timedelta(minutes=invite_object.period)
    if current_datetime > limit_datetime:
        return render(request,'web/invite_join.html',{'error':'邀请码已经过期'})

    if invite_object.count:
        if invite_object.use_count >= invite_object.count:
            return render(request,'web/invite_join.html',{'error':'邀请码数量已经使用完毕'})
        invite_object.use_count += 1
        invite_object.save()

    models.ProjectUser.objects.create(user=request.tracer.user,project=invite_object.project)
    invite_object.project.join_count += 1
    invite_object.save()

    return render(request,'web/invite_join.html',{'project':invite_object.project})



