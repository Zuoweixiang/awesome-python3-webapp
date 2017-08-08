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
async def index(request):
    users = await User.findAll()
    logging.info('users:%s',str(users))
    return {
        '__template__': 'test.html',
        'users': users
    }

