import hashlib
from django.conf import settings
import uuid

def md5(str):
    hash_object = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    hash_object.update(str.encode('utf-8'))
    return hash_object.hexdigest()

def file_id(string):
    data = "{}-{}".format(str(uuid.uuid4()),string)
    return md5(data)