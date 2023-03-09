from django import forms
from web.forms.bootstrap import  BootStrap
from web import models
from django.core.exceptions import ValidationError
from web.forms.widgets import ColorRadioSelect

class ProjectModelForm(BootStrap,forms.ModelForm):
    # name = forms.CharField(label="项目名称",max_length=32,error_messages={"required": "请输入项目名称","max_length":"项目名称最大长度不能超过32位"})
    bootstrap_class_exclude = ['color']
    def __init__(self,request,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.request = request
    class Meta:
        model = models.Project
        fields = ['name','color','desc']
        error_value = {"name":"项目名称","color":"项目颜色","desc":"项目描述"}
        error_messages = {}
        for field in fields:
            error_messages[field] = {"required":"%s不能为空"%(error_value[field])}

        widgets = {
            'desc': forms.Textarea,
            'color': ColorRadioSelect(attrs={"class":"color-radio"})
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        exitis = models.Project.objects.filter(name=name,creator=self.request.tracer.user).exists()
        if  exitis:
            raise ValidationError("该项目已存在！")

        count = models.Project.objects.filter(creator=self.request.tracer.user).count()

        if count >= self.request.tracer.price_policy.project_num:
            raise ValidationError("项目个数超出限制，请购买套餐！")

        return name
