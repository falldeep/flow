from django import forms
from web.forms.bootstrap import BootStrap
from web import models


class IssuesModelForm(BootStrap,forms.ModelForm):
    class Meta:
        model = models.Issues
        exclude = ['project','creator','create_datetime','latest_update_datetime']
        widgets = {
            "assign":forms.Select(attrs={"class":"selectpicker","data-live-search":"true"}),
            "attention": forms.SelectMultiple(attrs={"class":"selectpicker","data-live-search":"true","data-actions-box":"true"}),
            "issues_type": forms.Select(attrs={"class": "selectpicker"}),
            "module": forms.Select(attrs={"class": "selectpicker"}),
            "status": forms.Select(attrs={"class": "selectpicker"}),
            "priority": forms.Select(attrs={"class": "selectpicker"}),
            "parent": forms.Select(attrs={"class": "selectpicker","data-live-search":"true",}),

        }

        fields_list = ['subject', 'end_time', 'desc']
        error_value = {"subject": "标题", "end_time": "计划截止时间", "desc": "问题描述"}
        error_messages = {}
        for field in fields_list:
            error_messages[field] = {"required": "%s不能为空" % (error_value[field])}

    def __init__(self,request,issues_id=None,*args,**kwargs):
        super().__init__(*args,**kwargs)

        #1.获取当前项目的所有问题类型   数据格式[("id","xxxx")]
        self.fields['issues_type'].choices = models.IssuesType.objects.filter(
            project=request.tracer.project).values_list('id','title')

        #2.获取当前项目的所有模块
        models_list = [("", "还未选中任何项"), ]
        models_object_list = models.Module.objects.filter(project=request.tracer.project).values_list('id','title')
        models_list.extend(models_object_list)
        self.fields['module'].choices = models_list

        #3.指派和关注者
        #数据库找到当前项目的参与者和创建者
        total_user_list = [(request.tracer.project.creator_id,request.tracer.project.creator.username)]
        project_user_list = models.ProjectUser.objects.filter(project=request.tracer.project).values_list('user__id','user__username')
        total_user_list.extend(project_user_list)
        self.fields['assign'].choices = [("","未指派用户处理")]+total_user_list
        self.fields['attention'].choices = total_user_list

        #4.当前项目已创建的问题
        parent_list = [("","未指定父问题")]
        parent_object_list = models.Issues.objects.filter(project=request.tracer.project).values_list('id','subject')
        if  issues_id:
            exclude_self = models.Issues.objects.filter(id=issues_id).values_list('id','subject')
            parent_list.extend(parent_object_list)
            parent_list.remove(exclude_self[0])
        else:
            parent_list.extend(parent_object_list)
        self.fields['parent'].choices  = parent_list

class IssuesReplyModelForm(BootStrap,forms.ModelForm):
    class Meta:
        model = models.IssuesReply
        fields = ['content','reply']

class InviteModelForm(BootStrap,forms.ModelForm):
    class Meta:
        model = models.ProjectInvite
        fields = ['period','count']