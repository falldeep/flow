from django.template import Library
from web import models
from django.shortcuts import  reverse

register = Library()

@register.inclusion_tag('inclution/get_project.html')
def all_project_list(request):
    my_project_list = models.Project.objects.filter(creator=request.tracer.user)
    join_project_list = models.ProjectUser.objects.filter(user=request.tracer.user)
    return {"my":my_project_list,"join":join_project_list}

@register.inclusion_tag("inclution/menu_list_active.html")
def menu_list_active(request):
    menu_data_dict= [
        {"title": "概览","url": reverse("web:dashboard",kwargs={'project_id' : request.tracer.project.id})},
        {"title": "问题", "url": reverse("web:issues", kwargs={'project_id': request.tracer.project.id})},
        {"title": "统计", "url": reverse("web:statistics", kwargs={'project_id': request.tracer.project.id})},
        {"title": "文件", "url": reverse("web:file_list", kwargs={'project_id': request.tracer.project.id})},
        {"title": "wiki", "url": reverse("web:wiki", kwargs={'project_id': request.tracer.project.id})},
        {"title": "设置", "url": reverse("web:setting", kwargs={'project_id': request.tracer.project.id})},
    ]

    for item in menu_data_dict:
        if request.path_info.startswith(item['url']):
            item['class'] = "onl col-size"

    return {"menu_data_dict":menu_data_dict}
