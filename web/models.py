from django.db import models


# Create your models here.
class UserInfo(models.Model):
    """用户信息表"""
    username = models.CharField(verbose_name="用户名",max_length=32)
    email = models.EmailField(verbose_name="邮箱",max_length=32)
    mobile_phone = models.CharField(verbose_name="手机号",max_length=32)
    password = models.CharField(verbose_name="密码",max_length=32)
    """后续可以调整对应表结构来提升查询性能,默认情况下，用户注册时price_policy为空，则为免费用户，不为空则去对应的表中查询"""
    # price_policy = models.ForeignKey(verbose_name='价格策略',to='PricePolicy',null=True,blank=True)
    """后续项目个数也可以在中间件请求的时候将用户已经创建的个数获取出来，放到用户表"""
    def __str__(self):
        return self.username
class PricePolicy(models.Model):
    """价格策略表"""
    category_choices = (
        (1,'免费版'),
        (2,'收费版'),
        (3,'其他'),
    )

    category = models.SmallIntegerField(verbose_name="收费类型",default=2,choices=category_choices)
    title = models.CharField(verbose_name="标题",max_length=32)
    price = models.PositiveIntegerField(verbose_name="价格")

    project_num = models.PositiveIntegerField(verbose_name="项目数")
    project_member = models.PositiveIntegerField(verbose_name="项目成员数")
    project_space = models.PositiveIntegerField(verbose_name="单项目空间")
    project_file_size = models.PositiveIntegerField(verbose_name="单文件大小（M）")

    create_datetime = models.DateTimeField(verbose_name="创建时间",auto_now_add=True)

class Transaction(models.Model):
    """交易记录表"""
    status_choice = (
        (1,'未支付'),
        (2,'已支付'),
    )

    status = models.SmallIntegerField(verbose_name="交易状态",choices=status_choice)

    order = models.CharField(verbose_name="订单号",max_length=64,unique=True)

    user = models.ForeignKey(verbose_name="用户",to='UserInfo',on_delete=models.SET_NULL,null=True,blank=True)
    price_policy = models.ForeignKey(verbose_name="价格策略",to='PricePolicy',on_delete=models.SET_NULL,null=True,blank=True)

    count = models.IntegerField(verbose_name="数量/年",help_text="0表示无期限")

    price = models.IntegerField(verbose_name="实际支付价格")

    start_datetime = models.DateTimeField(verbose_name="开始时间",null=True,blank=True)
    end_datetime = models.DateTimeField(verbose_name="结束时间",null=True,blank=True)

    create_datetime = models.DateTimeField(verbose_name="创建时间",auto_now_add=True)

class Project(models.Model):
    """项目表"""
    COLOR_CHOICES = (
        (1,"#56b8eb"),
        (2, "#f20033"),
        (3, "#ebc656"),
        (4, "#a2d148"),
        (5, "#20BFA4"),
        (6, "#7461c2"),
        (7, "#20bfa3"),
    )

    name = models.CharField(verbose_name="项目名",max_length=32)
    color = models.SmallIntegerField(verbose_name="颜色",choices=COLOR_CHOICES,default=1)
    desc = models.CharField(verbose_name="描述",max_length=255,null=True,blank=True)
    use_space = models.IntegerField(verbose_name="项目已使用空间",default=0)
    stat = models.BooleanField(verbose_name="星标",default=False)

    join_count = models.SmallIntegerField(verbose_name="参与人数",default=1)
    creator = models.ForeignKey(verbose_name="创建者",to="UserInfo",on_delete=models.SET_NULL,null=True,blank=True)
    creator_dateTime = models.DateTimeField(verbose_name="创建时间",auto_now_add=True)

    bulcket = models.CharField(verbose_name="cos桶名称",max_length=128)
    region = models.CharField(verbose_name="cos区域",max_length=32)


class ProjectUser(models.Model):
    """项目参与者"""
    user = models.ForeignKey(verbose_name="参与者",to="UserInfo",on_delete=models.SET_NULL,null=True,blank=True)
    project = models.ForeignKey(verbose_name="项目",to="Project",on_delete=models.SET_NULL,null=True,blank=True)
    stat = models.BooleanField(verbose_name="星标",default=False)

    create_datetime = models.DateTimeField(verbose_name="加入时间",auto_now_add=True)

class Wiki(models.Model):
    """Wiki表"""
    project = models.ForeignKey(verbose_name="关联项目",to="Project",on_delete=models.CASCADE)
    title = models.CharField(verbose_name="标题",max_length=32)
    content = models.TextField(verbose_name="内容")
    depth = models.IntegerField(verbose_name="深度",default=1)


    #子关系，self可以替换为wiki，自己关联自己的主键ID
    parent = models.ForeignKey(verbose_name="父文章",to="self",null=True,blank=True,on_delete=models.CASCADE,related_name="childrer")
    def __str__(self):
        return self.title

class FileRepository(models.Model):
    """文件表"""
    project = models.ForeignKey(verbose_name="项目",to="Project",on_delete=models.CASCADE)
    file_type = models.CharField(max_length=30, choices=(('1', '文件'), ('2', '文件夹')), verbose_name="文件类型")


    name = models.CharField(verbose_name="文件夹名称",max_length=48,help_text="文件/文件夹名")
    key = models.CharField(verbose_name="文件存储在cos的key",max_length=128,null=True,blank=True)
    file_size = models.IntegerField(verbose_name="文件大小",null=True,blank=True)
    file_path = models.CharField(verbose_name="文件路径",max_length=255,null=True,blank=True)

    parent = models.ForeignKey(verbose_name="父目录",to="self",related_name="child",null=True,blank=True,on_delete=models.CASCADE)


    update_user = models.ForeignKey(verbose_name="最近更新者",to="UserInfo",on_delete=models.CASCADE)
    update_datetime = models.DateTimeField(verbose_name="更新时间",auto_now=True)

class Issues(models.Model):
    """问题表"""
    project = models.ForeignKey(verbose_name="项目",to="Project",on_delete=models.CASCADE)
    issues_type = models.ForeignKey(verbose_name="问题类型",to="IssuesType",on_delete=models.CASCADE)
    module = models.ForeignKey(verbose_name="模块",to="Module",null=True,blank=True,on_delete=models.CASCADE)

    subject = models.CharField(verbose_name="主题",max_length=80)
    desc = models.TextField(verbose_name="问题描述")
    priority_choices = (
        ("danger","高"),
        ("warning","中"),
        ("success","低"),
    )
    priority = models.CharField(verbose_name="优先级",max_length=32,choices=priority_choices,default='danger')

    status_choices = (
        ('1','新建'),
        ('2','处理中'),
        ('3','已解决'),
        ('4','已忽略'),
        ('5','待反馈'),
        ('6','已关闭'),
        ('7','重新打开'),
    )
    status = models.CharField(verbose_name="状态",max_length=32,choices=status_choices,default=1)
    assign = models.ForeignKey(verbose_name="指派",to="UserInfo",related_name="task",blank=True,null=True,on_delete=models.CASCADE)
    attention = models.ManyToManyField(verbose_name="关注者",to="UserInfo",related_name="observe",blank=True)
    start_time=models.DateField(verbose_name="开始时间",auto_now=True)
    end_time = models.DateField(verbose_name="结束时间")

    mode_choices = (
        (1,"公开模式"),
        (2,"隐私模式"),
    )

    mode=models.SmallIntegerField(verbose_name="模式",choices=mode_choices,default=1)
    parent =models.ForeignKey(verbose_name="父问题",to='self',related_name="child",null=True,blank=True,on_delete=models.SET_NULL)

    creator = models.ForeignKey(verbose_name="创建者",to="UserInfo",related_name="create_problems",on_delete=models.CASCADE)
    create_datetime = models.DateTimeField(verbose_name="创建时间",auto_now=True)
    latest_update_datetime = models.DateTimeField(verbose_name="最后更新时间",auto_now=True)

    def __str__(self):
        return self.subject


class Module(models.Model):
    "关联项目表"
    project = models.ForeignKey(verbose_name="项目",to="Project",on_delete=models.CASCADE)
    title = models.CharField(verbose_name="标题",max_length=128)
    def __str__(self):
        return self.title

class IssuesType(models.Model):
    """问题类型表"""
    PROJECT_INIT_LIST = ['任务','功能','BUG','需求']
    title=models.CharField(verbose_name="类型名称",max_length=32)
    project = models.ForeignKey(verbose_name="项目",to="Project",on_delete=models.CASCADE)
    def __str__(self):
        return self.title

class IssuesReply(models.Model):
   """问题回复"""
   reply_type_choices=(
       (1,'修改记录'),
       (2,'回复')
   )
   project = models.ForeignKey(verbose_name='关联项目',to="Project",on_delete=models.CASCADE)
   reply_type = models.IntegerField(verbose_name='类型', choices=reply_type_choices)
   issues = models.ForeignKey(verbose_name='问题', to='Issues',on_delete=models.CASCADE)
   content = models.TextField(verbose_name='描述')
   creator = models.ForeignKey(verbose_name='创建者', to='UserInfo', related_name='create_reply',on_delete=models.CASCADE)
   create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
   reply = models.ForeignKey(verbose_name='回复', to='self', null=True, blank=True,on_delete=models.CASCADE)


class ProjectInvite(models.Model):
    """项目邀请码"""
    project = models.ForeignKey(verbose_name="关联项目",to="Project",on_delete=models.CASCADE)
    code = models.CharField(verbose_name="邀请码",max_length=64,unique=True)
    count = models.PositiveIntegerField(verbose_name="限制数量",null=True,blank=True,help_text="空表示无限制")
    use_count = models.PositiveIntegerField(verbose_name="已邀请数量",default=True)
    period_choices = (
        (30,'30分钟'),
        (60,'1小时'),
        (300,'5小时'),
        (1440,'24小时'),
    )
    period = models.IntegerField(verbose_name='有效期',choices=period_choices,default=1440,)
    creator = models.ForeignKey(verbose_name='创建者',to='UserInfo',related_name='creator',on_delete=models.CASCADE)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)