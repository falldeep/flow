from  django.shortcuts import  render,redirect
from utils.cos import delete_bucket
from web import models

def setting(request,project_id):
    return render(request,'web/setting.html')

def delete(request,project_id):
    if request.method == "GET":
        return render(request,'web/setting_delete.html')

    project_name = request.POST.get('project_name')
    print(project_name,request.tracer.project.name)
    if not project_id or project_name != request.tracer.project.name:
        return render(request,"web/setting_delete.html",{'error':"项目名称错误"})

    #只有项目创建者有权删除
    if request.tracer.user != request.tracer.project.creator:
        return render(request,'web/setting_delete.html',{'error':"无权删除该项目"})

    #1.删除文件、碎片、桶
    delete_bucket(bucket=request.tracer.project.bulcket,region=request.tracer.project.region)
    models.Project.objects.filter(id=request.tracer.project.id).delete()

    return redirect("web:project_list")