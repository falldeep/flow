"""flow URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path,include,re_path
from web.views import account,home,project,manage,wiki,file,seeting,issues,dashboard,pay

urlpatterns = [
    path('register/',account.register,name='register'),
    path('send/sms/',account.send_sms,name='send_sms'),
    path('login_sms',account.login_sms,name='login_sms'),
    path('login/',account.login,name='login'),
    path('img_code',account.img_code,name='img_code'),
    path('home/',home.index,name="home"),
    path('logout/',account.logout,name="logout"),

    path('project/list',project.project_list,name="project_list"),
    re_path(r'project/stat/(?P<project_type>\w+)/(?P<project_id>\d+)/',project.project_stat,name="project_stat"),
    re_path(r'project/unstat/(?P<project_type>\w+)/(?P<project_id>\d+)/',project.project_unstat,name="project_unstat"),

    re_path(r'manage/(?P<project_id>\d+)/',include([
        path('dashboard/',dashboard.dashboard,name="dashboard"),
        path('dashboard/chart',dashboard.chart,name="dashboard_chart"),

        path('statistics/',manage.statistics,name="statistics"),
        path('statistics/statistics_priority',manage.statistics_priority,name="statistics_priority"),
        path('statistics/statistics_project_user', manage.statistics_project_user, name="statistics_project_user"),



        path('wiki/',wiki.wiki,name="wiki"),
        path('wiki/add',wiki.wiki_add,name="wiki_add"),



        path("wiki/wiki_catalog",wiki.wiki_catalog,name="wiki_catalog"),
        re_path("wiki/delete/(?P<wiki_id>\d+)/",wiki.wiki_delete,name="wiki_delete"),
        re_path("wiki/edit/(?P<wiki_id>\d+)/",wiki.wiki_edit,name="wiki_edit"),
        path("wiki/img_upload",wiki.wiki_upload,name="wiki_upload"),

        path('file/',file.file_list,name="file_list"),
        path('file/del/',file.file_del,name="file_del"),
        path('cos/cos_credential/',file.cos_credential,name="cos_credential"),
        path('file/post/',file.file_post,name="file_post"),
        re_path('file/download/(?P<file_id>\d+)/',file.download,name="file_download"),


        path('setting/',seeting.setting,name="setting"),
        path('setting/delete',seeting.delete,name="setting_delete"),

        path('issues/',issues.issues,name="issues"),
        re_path('issues/detail/(?P<issues_id>\d+)/',issues.detail,name="issues_detail"),
        re_path('issues/record/(?P<issues_id>\d+)/', issues.record, name="issues_record"),
        re_path('issues/change/(?P<issues_id>\d+)/', issues.change, name="issues_change"),
        path('issues/ivivte_url/',issues.invite_url,name="invite_url")
    ],None),None),

    re_path(r'^ivivte/join/(?P<code>\w+)/', issues.invite_join, name='invite_join'),

    path('price/',pay.price,name='price'),
    re_path('payment/(?P<policy_id>\d+)/',pay.payment,name="payment"),
    path('pays/',pay.pays,name='pays')

]
