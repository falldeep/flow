from web.scripts import base
from  web import models


def free():
    exitis = models.PricePolicy.objects.filter(category=1,title="个人免费版").exists()
    if not exitis:
        models.PricePolicy.objects.create(
        category=1,
        title="个人免费版",
        price=0,
        project_num=3,
        project_member=2,
        project_space=20,
        project_file_size=5,
        )

def vip():
    exitis = models.PricePolicy.objects.filter(category=2, title="VIP").exists()
    if not exitis:
        models.PricePolicy.objects.create(
        category=2,
        title="VIP",
        price=100,
        project_num=10,
        project_member=10,
        project_space=10,
        project_file_size=20,
        )

def svip():
    exitis = models.PricePolicy.objects.filter(category=2, title="SVIP").exists()
    if not exitis:
        models.PricePolicy.objects.create(
        category=2,
        title="SVIP",
        price=150,
        project_num=20,
        project_member=20,
        project_space=20,
        project_file_size=40,
        )

def supervip():
    exitis = models.PricePolicy.objects.filter(category=2, title="终生荣誉VIP").exists()
    if not exitis:
        models.PricePolicy.objects.create(
        category=2,
        title="终生荣誉VIP",
        price=999,
        project_num=999,
        project_member=999,
        project_space=999,
        project_file_size=999,
        )


if __name__ == '__main__':
      free()
      vip()
      svip()
      supervip()