from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,redirect,reverse
from web.forms.file import FileModelForm,FileModelFormCC
from web import models
from utils.cos import  file_delete,batch_file_delete
from django.views.decorators.csrf import  csrf_exempt
from utils.cos import credential
import json
import requests

def file_list(request,project_id):
    """获取文件及文件夹"""
    parent_object = None
    folder_id = request.GET.get("folder","")

    if folder_id.isdecimal():
        parent_object = models.FileRepository.objects.filter(id=int(folder_id), file_type=2,
                                                             project=request.tracer.project).first()

    if request.method == "GET":
        baeadcrumb_list = []
        parent = parent_object
        while parent:
            # baeadcrumb_list.insert(0,model_to_dict(parent_object,['id','name']))
            baeadcrumb_list.insert(0,{"id":parent.id,"name":parent.name})
            parent = parent.parent

        queryset = models.FileRepository.objects.filter(project=request.tracer.project)

        if parent_object:
            file_object = queryset.filter(parent=parent_object).order_by("-file_type")
        else:
            file_object = queryset.filter(parent__isnull=True).order_by("-file_type")

        form = FileModelForm(request, parent_object)
        return render(request,"web/file.html",{"form":form,"file_object":file_object,
                                               "baeadcrumb_list":baeadcrumb_list,
                                               "folder_object":parent_object})



    fid = request.POST.get('fid','')
    if fid.isdecimal():
        edit_object = models.FileRepository.objects.filter(id=int(fid), file_type=2,
                                                             project=request.tracer.project).first()
        form = FileModelForm(request, parent_object, data=request.POST,instance=edit_object)
    else:
        form = FileModelForm(request, parent_object, data=request.POST)

    if form.is_valid():
       form.instance.project = request.tracer.project
       form.instance.file_type = 2
       form.instance.update_user = request.tracer.user
       form.instance.parent = parent_object
       form.save()
       return JsonResponse({"status":True})

    return JsonResponse({"status":False,"error":form.errors})


def file_del(request,project_id):
    """删除文件和文件夹"""

    fid = request.GET.get("fid","")
    del_object = None
    if fid.isdecimal():
        del_object = models.FileRepository.objects.filter(id=fid,project=request.tracer.project).first()

    #如果是文件直接删除并返还空间
    if del_object.file_type == 1:
        request.tracer.project.use_space -= del_object.file_size
        request.tracer.project.save()
        del_object.delete()
        return JsonResponse({"status":True})

    #如果是文件夹（循环遍历文件夹，目录直接删除，如果是文件则返还空间，并删除）
    total_size = 0
    folder_list = [del_object]
    key_list = []
    for folder in folder_list:
        child_list = models.FileRepository.objects.filter(
            project=request.tracer.project,parent=folder
        ).order_by("-file_type")
        for child in child_list:
            if child.file_type == "2":
                #如果是文件
               folder_list.append(child)
            else:
                total_size += child.file_size
                #file_delete(request.tracer.project.bulcket,request.tracer.project.region,child.key)
                key_list.append(child.key)

    #cos批量删除
    if key_list:
        batch_file_delete(request.tracer.project.bulcket,request.tracer.project.region,key_list)

    #返还项目空间
    if total_size:
        request.tracer.project.use_space -= total_size
        request.tracer.project.save()


    del_object.delete()
    return JsonResponse({'status':True})

@csrf_exempt
def cos_credential(request,project_id):
    """获取用户COS上传临时凭证"""

    #颁发凭证前进行容量判断
    per_file_limit = request.tracer.prece_policy.pre_file_size * 1024 * 1024
    total_file_limit = request.tracer.prece_policy.project_space * 1024 * 1024 * 1025
    total_size = 0
@csrf_exempt
def cos_credential(request, project_id):
    """ 获取cos上传临时凭证 """
    per_file_limit = request.tracer.price_policy.project_file_size * 1024 * 1024
    total_file_limit = request.tracer.price_policy.project_space * 1024 * 1024 * 1024

    total_size = 0
    file_list = json.loads(request.body.decode('utf-8'))
    for item in file_list:
        # 文件的字节大小 item['size'] = B
        # 单文件限制的大小 M
        # 超出限制
        if item['size'] > per_file_limit:
            msg = "单文件超出限制（最大{}M），文件：{}，请升级套餐。".format(request.tracer.price_policy.project_file_size, item['name'])
            return JsonResponse({'status': False, 'error': msg})
        total_size += item['size']

        # 做容量限制：单文件 & 总容量

    # 总容量进行限制
    # request.tracer.price_policy.project_space  # 项目的允许的空间
    # request.tracer.project.use_space # 项目已使用的空间
    if request.tracer.project.use_space + total_size > total_file_limit:
        return JsonResponse({'status': False, 'error': "容量超过限制，请升级套餐。"})

    data_dict = credential(request.tracer.project.bulcket, request.tracer.project.region)
    return JsonResponse({'status': True, 'data': data_dict})


@csrf_exempt
def file_post(request, project_id):
    """ 已上传成功的文件写入到数据 """
    """
    name: fileName,
    key: key,
    file_size: fileSize,
    parent: CURRENT_FOLDER_ID,
    # etag: data.ETag,
    file_path: data.Location
    """

    # 根据key再去cos获取文件Etag和"db7c0d83e50474f934fd4ddf059406e5"

    # 把获取到的数据写入数据库即可
    form = FileModelFormCC(request, data=request.POST)
    if form.is_valid():
        # 通过ModelForm.save存储到数据库中的数据返回的isntance对象，无法通过get_xx_display获取choice的中文
        # form.instance.file_type = 1
        # form.update_user = request.tracer.user
        # instance = form.save() # 添加成功之后，获取到新添加的那个对象（instance.id,instance.name,instance.file_type,instace.get_file_type_display()

        # 校验通过：数据写入到数据库
        data_dict = form.cleaned_data
        data_dict.pop('etag')
        data_dict.update({'project': request.tracer.project, 'file_type': 1, 'update_user': request.tracer.user})
        instance = models.FileRepository.objects.create(**data_dict)

        # 项目的已使用空间：更新 (data_dict['file_size'])
        request.tracer.project.use_space += data_dict['file_size']
        request.tracer.project.save()

        if instance.get_file_type_display() == 1:
            file_type = "文件"
        else:
            file_type = "文件夹"

        result = {
            'id': instance.id,
            'name': instance.name,
            'file_size': instance.file_size,
            'username': instance.update_user.username,
            'datetime': instance.update_datetime.strftime("%Y年%m月%d日 %H:%M"),
            'download_url': reverse('web:file_download', kwargs={"project_id": project_id, 'file_id': instance.id}),
            'file_type': file_type
        }
        return JsonResponse({'status': True, 'data': result})

    return JsonResponse({'status': False, 'data': "文件错误"})


def download(request,project_id,file_id):
    file_object = models.FileRepository.objects.filter(id=file_id).first()
    res = requests.get(file_object.file_path)
    data = res.iter_content()

    response = HttpResponse(data,content_type='application/octet-stream')

    # 设置响应头：中文文件名转义
    response["Content-Disposition"] = "attachment; filename={}".format(file_object.name)
    return response
