from django.shortcuts import  render
from web.forms.project import ProjectModelForm
from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,redirect
from web import models
import time
from utils.cos import cos_create_bucket
def project_list(request):
    if request.method == "GET":
        form = ProjectModelForm(request,request.GET)
        project_dict = {'my':[],'join':[],'stat':[]}

        my_project = models.Project.objects.filter(creator=request.tracer.user)
        for item in my_project:
            if item.stat:
                project_dict['stat'].append({"value":item,"type":"my"})
            else:
                project_dict['my'].append(item)

        join_project = models.ProjectUser.objects.filter(user=request.tracer.user)
        for item in join_project:
            if item.stat:
                project_dict['stat'].append({"value":item.project,"type":"join"})
            else:
                project_dict['join'].append(item.project)


        return render(request,'web/project_list.html',{'form':form,'project_dict':project_dict})


    form = ProjectModelForm(request,data=request.POST)
    if  form.is_valid():
            now = time.localtime()
            region = "ap-beijing"
            cos_backet_name = "{}-{}-1300755188".format(request.tracer.user.mobile_phone,time.strftime("%Y%m%d%H%M%S",now))

            cos_create_bucket(cos_backet_name,region)

            form.instance.creator = request.tracer.user
            form.instance.bulcket = cos_backet_name
            form.instance.region = region

            instance = form.save()

            issues_type_object_list = []
            for item in models.IssuesType.PROJECT_INIT_LIST:
                issues_type_object_list.append(models.IssuesType(project=instance,title=item))
            models.IssuesType.objects.bulk_create(issues_type_object_list)


            return JsonResponse({'status':True})
    return JsonResponse({'status':False,'error':form.errors})


def project_stat(request,project_type,project_id):
    if project_type == "my":
       models.Project.objects.filter(id=project_id,creator=request.tracer.user).update(stat=True)
       return redirect('web:project_list')
    if project_type == "join":
       models.ProjectUser.objects.filter(id=project_id, user=request.tracer.user).update(stat=True)
       return redirect('web:project_list')

    return HttpResponse("请求错误")

def project_unstat(request,project_type,project_id):
    if project_type == "my":
        models.Project.objects.filter(id=project_id,creator=request.tracer.user).update(stat=False)
        return redirect('web:project_list')
    if project_type == "join":
        models.ProjectUser.objects.filter(id=project_id,user=request.tracer.user).update(stat=False)
        return redirect('web:project_list')

    return HttpResponse("请求错误")