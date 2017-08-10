#@author: ziven.mac 
#@contact: xiangzuowei@gomeplus.com.cn
#@site: www.gomeple.com
#@version: 1.0
#@license: Apache Licence
#@file: handlers.py
#@time: 2017/8/7 14:50


'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post

from model import User,Comment, Blog, next_id

@get('/')
def index(request):
    logging.info('handles:index call........')
    users = yield from User.findAll()
    logging.info('handles:index call::%s' % type(users))
    return {
        '__template__': 'test.html',
        'users': users
    }

# @get('/')
# async def handler_url_blog(request):
#     body='<h1>Awesome</h1>'
#     return body
# @get('/greeting')
# async def handler_url_greeting(*,name,request):
#     body='<h1>Awesome: /greeting %s</h1>'%name
#     return body