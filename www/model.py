#@author: ziven.mac 
#@contact: xiangzuowei@gomeplus.com.cn
#@site: www.gomeplue.com
#@version: 1.0
#@license: Apache Licence
#@file: model.py
#@time: 2017/8/2 10:07
import  time,uuid
from orm import Model,StringField,BooleanField,FloatField,TextField

def next_id():
    return '%015d%s000' % (int(time.time()*1000),uuid.uuid4().hex)
class User(Model):
    __table__ = 'users'
    id = StringField(primary_key = True,default=next_id(),ddl = 'varchar(50)')
    email = StringField(ddl = 'varchar(50)')
    passwd = StringField(ddl = 'varchar(50)')
    admin = BooleanField()
    name = StringField(ddl = 'varchar(50)')
    image = StringField(ddl = 'varchar(500)')
    created_at = FloatField(default = time.time())

class Blog(Model):
    __table__ = 'blogs'
    id = StringField(primary_key = True,default = next_id(),ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_name = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(50)')
    name = StringField(ddl = 'varchar(50)')
    summary = StringField(ddl= 'varchar(50)')
    content = TextField()
    create_at = FloatField(default = time.time())

class Comment(Model):
    __table = 'comments'
    id = StringField(primary_key = True,default = next_id(),ddl = 'varchar(50)')
    blog_id = StringField(ddl = 'varchar(50)')
    user_id = StringField(ddl = 'varchar(50)')
    user_image = StringField(ddl = 'varchar(500)')
    content = TextField()
    create_at = FloatField(default = time.time())
