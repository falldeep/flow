from django.urls import path,include,re_path
from app import views

urlpatterns = [
    path('project_list',views.project_list,name='project_list')
]