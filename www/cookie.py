

from config import configs


import re, time, json, logging, hashlib, base64, asyncio
import  markdown2

from aiohttp import web

from coroweb import get, post

from apis import  APIValueError,APIResourceNotFoundError,APIError,APIPermissionError

from model import User,Comment, Blog, next_id


# COOKIE_NAME = 'awesession'
COOKIE_KEY =   configs.session.secret



def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        return
        raise APIPermissionError()

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p<1:
        p =1
    return p


def user2cookie(user,max_age):
    expires = str(int(time.time()+max_age))
    s = '%s-%s-%s-%s' %(user.id,user.passwd,expires,COOKIE_KEY)
    L =[user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)
@asyncio.coroutine
def cookie2user(cookie_str):
    if not  cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L)!=3:
            return None
        uid,expires,sha1 =L
        if int(expires)<time.time():
            return None
        user_arr = yield from User.findAll('id=?',[uid])

        if user_arr is None:
            return None
        user = user_arr[0]
        s = '%s-%s-%s-%s' %(user.id,user.passwd,expires,COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1...')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None