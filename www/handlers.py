#@author: ziven.mac 
#@contact: xiangzuowei@gomeplus.com.cn
#@site: www.gomeple.com
#@version: 1.0
#@license: Apache Licence
#@file: handlers.py
#@time: 2017/8/7 14:50


'url handlers'

import re, time, json, logging, hashlib, base64, asyncio
import  markdown2

from aiohttp import web

from coroweb import get, post

from apis import  APIValueError,APIResourceNotFoundError,APIError

from model import User,Comment, Blog, next_id

from config import configs

# COOKIE_NAME = 'awesession'
# COOKIE_KEY = configs.session.secrect





@get('/')
def index(request):
    logging.info('handles:index call........')
    users = yield from User.findAll()
    logging.info('handles:index call::%s' % type(users))
    return {
        '__template__': 'test.html',
        'users': users
    }


@get('/blogs')
def handler_url_blogs(request):
    summary = 'lorem issum dolor sit amet ,consectetur adipisicing elit ,sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id = '1',name = 'Test Blog',summary = summary,created_at = time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time() - 3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time() - 7200)
    ]
    return {
        '__template__':'blogs.html',
        'blogs':blogs
    }

@get('/register')
def register():
    return {
        '__template__':'register.html'
    }

@get('/api/users/')
def api_users():
    return 'redirect:/api/users'

@get('/api/users')
def get_users(request):
    users = yield from User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    return dict(users=users)

@get('/api/users/{id}')
def api_get_users(id,request):
    # page_index = get_page_index(page)
    # num = yield from User.findNumber('count(id)')
    # p = Page(num, page_index)
    # if num == 0:
    #     return dict(page=p, users=())
    logging.info('handles call:/api/users ....')
    users = yield from User.findAll(orderBy='created_at desc', limit=10 ,where = 'id=\'%s\'' % id  )
    for u in users:
        u.passwd = '******'
    return dict( users=users)


_RE_EMAILL = re.compile(r'^[a-z0-9\.\-\_]+@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 =  re.compile(r'^[0-9a-f]{40}$')

#register user
@post('/api/users')
def api_register_user(*,email,name,passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not  email or not _RE_EMAILL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = yield from User.findAll('email=?',[email])
    if len(users)>0:
        raise APIError('register:failed','email','email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s'%(uid,passwd)
    user = User(id = uid,name = name.strip(),email = email,passwd = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),image='http://www.gravatar.com/avatar/%s?d=mm&s=120'%hashlib.md5(email.encode('utf-8')).hexdigest() )
    yield from user.save()

    #make session cookie
    r = web.json_response()
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user,ensure_ascii=False).encode('utf-8')
    return r
