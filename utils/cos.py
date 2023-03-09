# -*- coding: UTF-8 -*-
'''=================================================
@Project -> File   ：MyDjango -> cos_upload_demo
@IDE    ：PyCharm
@Author ：ruochen
@Date   ：2023/1/9 11:52
@Desc   ：
=================================================='''

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from django.conf import settings
from qcloud_cos.cos_exception import CosServiceError

def cos_create_bucket(bucket,region="ap-beijing"):
	"""
	腾讯云cos 创建桶
	:param backet: 桶名称
	:param region: 桶地域
	:return:
	"""

	config = CosConfig(Region=region, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
	client = CosS3Client(config)

	response = client.create_bucket(
		Bucket=bucket,  #后缀数字为appid
		ACL="public-read"  # private / public-read /public-read-write
	)
	# 设置cors的规则，
	cors_config = {
		'CORSRule': [
			{
				'AllowedOrigin': '*',
				'AllowedMethod': ['GET', 'PUT', 'HEAD', 'POST', 'DELETE'],
				'AllowedHeader': "*",
				'ExposeHeader': "*",
				'MaxAgeSeconds': 500
			}
		]
	}
	client.put_bucket_cors(
		Bucket=bucket,
		CORSConfiguration=cors_config
	)


def cos_upload_file(backet,region,file_object,key):
	"""
	腾讯云cos 上传文件
	:param backet: 桶名称
	:param region: 桶地域
	:param file_object 文件对象
	:param key 存储到桶之后的名称
	:return:
	"""
	config = CosConfig(Region=region, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
	client = CosS3Client(config)

	response = client.upload_file_from_buffer(
		Bucket=backet,
		Body=file_object,  # 本地文件的路径
		Key=key,  # 上传到桶之后的文件名
	)

def cos_object_url(backet,region,key):
	"""
	腾讯云cos 获取url
	:param backet: 桶名称
	:param region: 桶地域
	:param key: 对象名称
	:return:
	"""
	config = CosConfig(Region=region, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
	client = CosS3Client(config)

	# 生成URL
	url = client.get_object_url(
		Bucket=backet,
		Key=key,
	)
	return url

def file_delete(backet,region,key):
	"""
	腾讯云cos 删除文件
	:param backet: 桶名称
	:param region: 桶地域
	:param key: 对象名称
	:return:
	"""
	config = CosConfig(Region=region, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
	client = CosS3Client(config)
	client.delete_object(
		Bucket=backet,
		Key=key,
	)

def batch_file_delete(backet,region,key_list):
	"""
	腾讯云cos 批量删除文件
	:param backet: 桶名称
	:param region: 桶地域
	:param key: 对象列表
	:return:
	"""
	config = CosConfig(Region=region, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
	client = CosS3Client(config)
	objects = {
		"Quiet": "true",
		"Object": key_list
	}
	client.delete_objects(
		Bucket=backet,
		Delete=objects,
	)

def credential(bucket, region):
    """ 获取cos上传临时凭证 """

    from sts.sts import Sts

    config = {
        # 临时密钥有效时长，单位是秒（30分钟=1800秒）
        'duration_seconds': 5,
        # 固定密钥 id
        'secret_id': settings.COS_SECRET_ID,
        # 固定密钥 key
        'secret_key': settings.COS_SECRET_KEY,
        # 换成你的 bucket
        'bucket': bucket,
        # 换成 bucket 所在地区
        'region': region,
        # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
        # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
        'allow_prefix': '*',
        # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
        'allow_actions': [
            # "name/cos:PutObject",
            # 'name/cos:PostObject',
            # 'name/cos:DeleteObject',
            # "name/cos:UploadPart",
            # "name/cos:UploadPartCopy",
            # "name/cos:CompleteMultipartUpload",
            # "name/cos:AbortMultipartUpload",
            "*",
        ],

    }

    sts = Sts(config)
    result_dict = sts.get_credential()
    return result_dict

def check_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
    client = CosS3Client(config)

    data = client.head_object(
        Bucket=bucket,
        Key=key
    )

    return data

def delete_bucket(bucket, region):
	""" 删除桶 """
	config = CosConfig(Region=region, SecretId=settings.COS_SECRET_ID, SecretKey=settings.COS_SECRET_KEY)
	client = CosS3Client(config)
	try:
		# 找到 文件 & 删除
		while 1:
			# 先找到桶中所有文件
			# 每次只获取1000个文件
			part_objects = client.list_objects(bucket)
			contents = part_objects.get("Contents")
			if not contents:
				# 已经删除完毕，为空值
				break
			# 批量删除
			objects = {
				"Quiet": "true",
				"Object": [{"Key": item["Key"]} for item in contents]
			}
			client.delete_objects(bucket, objects)
			#
			if part_objects['IsTruncated'] == "false":
				break

		# 找到 碎片 & 删除
		while 1:
			part_uploads = client.list_multipart_uploads(bucket)
			uploads = part_uploads.get('Upload')
			if not uploads:
				break
			for item in uploads:
				client.abort_multipart_upload(bucket, item['Key'], item['UploadId'])
			if part_uploads['IsTruncated'] == "false":
				break
		# 删除桶
		client.delete_bucket(bucket)
	except CosServiceError as e:
		pass
