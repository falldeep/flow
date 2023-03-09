import collections
from django.shortcuts import  render
from django.db.models import Count
from django.http import JsonResponse
from web import models

def statistics(request,project_id):
    """问题类型数量"""
    status_dict = collections.OrderedDict()
    for key,text in models.Issues.status_choices:
        status_dict[key] = {'text':text,'count':0}
    issues_data = models.Issues.objects.filter(project_id=project_id).values('status').annotate(ct=Count('id'))
    for item in issues_data:
        status_dict[item['status']]['count'] = item['ct']
    return render(request,'web/statistics.html',{'status_dict':status_dict})

def statistics_priority(request,project_id):
    """ 按优先级生成饼图数据
    数据格式要求：[{'name': '高', 'y': 13}, {'name': '中', 'y': 0}, {'name': '低', 'y': 1}]
    """

    start = request.GET.get('start')
    end = request.GET.get('end')


    data_dict = collections.OrderedDict()
    for key, text in models.Issues.priority_choices:
        data_dict[key] = {'name': text, 'y': 0}

    result = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start,
                                          create_datetime__lt=end).values('priority').annotate(ct=Count('id'))

    for item in result:
        data_dict[item['priority']]['y'] = item['ct']

    return JsonResponse({'status': True, 'data': list(data_dict.values())})

def statistics_project_user(request, project_id):
    """项目成员分配任务数量视图
    数据格式要求：categories: ['小明', '小红', 'alx']
    series: [{
        name: '新建',
        status: [1, 2,3]
    }, {
        name: '完成',
        status: [2, 3, 5]
    """
    start = request.GET.get('start')
    end = request.GET.get('end')
    all_user_dict = collections.OrderedDict()
    all_user_dict[request.tracer.project.creator.id] = {
        'name': request.tracer.project.creator.username,
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }

    all_user_dict[None] = {
        'name': '未指派',
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }


    user_list = models.ProjectUser.objects.filter(project_id=project_id)
    for item in user_list:
        all_user_dict[item.user_id] = {
            'name': item.user.username,
            'status': {item[0]: 0 for item in models.Issues.status_choices}
        }


    issues = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start, create_datetime__lt=end)

    for item in issues:
        if not item.assign:
            all_user_dict[None]['status'][item.status] += 1
        else:
            all_user_dict[item.assign_id]['status'][item.status] += 1


    categories = [data['name'] for data in all_user_dict.values()]


    data_result_dict = collections.OrderedDict()
    for item in models.Issues.status_choices:
        data_result_dict[item[0]] = {'name': item[1], 'data': []}

    for key, text in models.Issues.status_choices:
        for row in all_user_dict.values():
            count = row['status'][key]
            data_result_dict[key]['data'].append(count)

    content = {
        'status': True,
        'data': {
            'categories': categories,
            'series': list(data_result_dict.values())
        },
    }
    return JsonResponse(content)

