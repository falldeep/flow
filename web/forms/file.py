from django import forms
from web import models
from web.forms.bootstrap import  BootStrap
from django.core.exceptions import ValidationError
from utils.cos import check_file,cos_object_url


class FileModelForm(BootStrap,forms.ModelForm):
    class Meta:
        model = models.FileRepository
        fields = ['name']

    def __init__(self,request,parent_object,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.request = request
        self.parent_object = parent_object


    def clean_name(self):
        file_name = self.cleaned_data['name']
        queryset = models.FileRepository.objects.filter(file_type=2, name=file_name, project=self.request.tracer.project)

        if self.parent_object:
            exist = queryset.filter(parent=self.parent_object).exists()
        else:
            exist = queryset.filter(parent__isnull=True).exists()

        if exist:
            raise  ValidationError("文件夹已存在")
        return file_name

class FileModelFormCC(BootStrap,forms.ModelForm):
    etag = forms.CharField(label='ETag')

    class Meta:
        model = models.FileRepository
        exclude = ['project','file_type','update_user','update_datetime']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request


    def clean_file_path(self):
        key = self.cleaned_data['key']
        url = cos_object_url(
            backet=self.request.tracer.project.bulcket,
            region=self.request.tracer.project.region,
            key=key , )
        # return "https://{}".format(self.cleaned_data['file_path'])
        return url

    def clean(self):
        key = self.cleaned_data['key']
        etag = self.cleaned_data['etag']
        size = self.cleaned_data['file_size']

        if not key or not etag:
            return self.cleaned_data

        # 向COS校验文件是否合法
        # SDK的功能
        from qcloud_cos.cos_exception import CosServiceError
        try:
            result = check_file(self.request.tracer.project.bulcket, self.request.tracer.project.region, key)
        except CosServiceError as e:
            self.add_error("key", '文件不存在')
            return self.cleaned_data

        cos_etag = result.get('ETag')
        if etag != cos_etag:
            self.add_error('etag', 'ETag错误')

        cos_length = result.get('Content-Length')
        if int(cos_length) != size:
            self.add_error('size', '文件大小错误')

        return self.cleaned_data



