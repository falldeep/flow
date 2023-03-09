from django.shortcuts import render,HttpResponse

# Create your views here.
def project_list(request):
    return render(request, "app/project_list.html")