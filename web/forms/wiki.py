from django import forms
from web import models
from web.forms.bootstrap import  BootStrap

class WikiModelForm(BootStrap,forms.ModelForm):
    class Meta:
        model= models.Wiki
        exclude = ['project','depth']
        widgets = {
            'content': forms.Textarea,}

    def __init__(self,request,wiki_id=None,*args,**kwargs):
        super().__init__(*args,**kwargs)

        total_data_list = [("","选择上一级文章")]
        data_list = models.Wiki.objects.filter(project=request.tracer.project).values_list('id','title')
        if wiki_id:
            exclude_self = models.Wiki.objects.filter(id=wiki_id).values_list('id','title')
            total_data_list.extend(data_list)
            total_data_list.remove(exclude_self[0])
        else:
            total_data_list.extend(data_list)
        self.fields['parent'].choices = total_data_list
