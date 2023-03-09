from django.http import JsonResponse
from django.shortcuts import render,HttpResponse,redirect,reverse
from web.forms.wiki import WikiModelForm
from web import models
from django.views.decorators.csrf import csrf_exempt
from utils.encrypt import file_id
from utils.cos import cos_upload_file,cos_object_url
from django.views.decorators.clickjacking import xframe_options_sameorigin

def wiki(request,project_id):
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, "web/wiki.html")

    wiki_object = models.Wiki.objects.filter(id=wiki_id,project_id=project_id).first()
    return render(request,"web/wiki.html",{'wiki_object':wiki_object})

def wiki_add(request,project_id):
    if request.method == "GET":
        form = WikiModelForm(request)
        return render(request, "web/wiki_add.html", {"form":form})

    form = WikiModelForm(request,data=request.POST)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.instance.project = request.tracer.project
        form.save()
        url = reverse('web:wiki', kwargs={'project_id': project_id})
        return redirect(url)

    return render(request, "web/wiki_add.html", {"form":form})


def wiki_catalog(request,project_id):
    data = models.Wiki.objects.filter(project_id=project_id).values("id","title","parent_id").order_by("depth","id")
    return JsonResponse({"status":True,"data":list(data)})


def wiki_delete(request,project_id,wiki_id):
    models.Wiki.objects.filter(project_id=project_id,id=wiki_id).delete()

    url = reverse('web:wiki', kwargs={'project_id': project_id})
    return redirect(url)

def wiki_edit(request,project_id,wiki_id):
    wiki_object = models.Wiki.objects.filter(project_id=project_id,id=wiki_id).first()
    if not wiki_object:
        url = reverse('web:wiki', kwargs={'project_id': project_id})
        return redirect(url)

    if request.method == "GET":
        form = WikiModelForm(request,wiki_id,instance=wiki_object)
        return render(request,"web/wiki_add.html",{"form":form})

    form = WikiModelForm(request,wiki_id,data=request.POST, instance=wiki_object)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.save()
        url = reverse('web:wiki', kwargs={'project_id': project_id})
        preview_url = "{0}?wiki_id={1}".format(url,wiki_id)
        return redirect(preview_url)

    return render(request, "web/wiki_add.html", {"form": form})

@csrf_exempt
@xframe_options_sameorigin
def wiki_upload(request,project_id):

    result = {
        'success': 0,
        'message': None,
        'url':None,
    }

    file_objet = request.FILES.get("editormd-image-file")
    file_suffix = file_objet.name.rsplit(".")[-1]
    if not file_objet:
       result["message"] = "图片获取失败"
       return JsonResponse(result)

    upload_file_name = "{}.{}".format(file_id(request.tracer.user.mobile_phone),file_suffix)

    backet = request.tracer.project.bulcket
    region = request.tracer.project.region


    cos_upload_file(
        backet=backet,
        region=region,
        file_object=file_objet,
        key=upload_file_name,
    )

    url = cos_object_url(
        backet=backet,
        region=region,
        key=upload_file_name,)

    result["success"] = 1
    result["url"] = url
    return JsonResponse(result)



