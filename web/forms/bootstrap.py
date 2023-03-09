from django.forms.fields import Field
from django.forms import fields
class BootStrap:
    bootstrap_class_exclude = []
    # Field.default_error_messages = {
    #     'required': ('不能为空'),
    # }
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name,field in self.fields.items():
            if name in self.bootstrap_class_exclude:
                continue
            old_class = field.widget.attrs.get('class',"")
            field.widget.attrs['class'] = "{} form-control".format(old_class)
            field.widget.attrs['placeholder'] = "请输入%s" % (field.label)
            field.widget.attrs['autocomplete']="off"
            field.widget.attrs["is_required"] = "这个是不能为空的"

