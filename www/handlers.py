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

from apis import  APIValueError, APIResourceNotFoundError, APIError, Page,APIPermissionError

from model import User, Comment, Blog, next_id

from cookie import COOKIE_KEY, user2cookie, cookie2user, check_admin, get_page_index,text2html


@get('/')
def index(request):

    blogs= yield from  Blog.findAll()

    return {
        '__template__': 'blogs.html',
        'blogs': blogs,
        '__user__':request.__user__
    }


@get('/blogs')
def handler_url_blogs(request):
    blogs = yield from  Blog.findAll()
    return {
        '__template__':'blogs.html',
        'blogs':blogs
    }

@get('/blog/{id}')
def get_blog(id,request):
    blog = yield from Blog.find(id)
    comments = yield from Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        '__user__':request.__user__,
        'comments': comments
    }




@get('/register')
def register():
    return {
        '__template__':'register.html'
    }

@get('/signin')
def signin():
    return {
        '__template__':'signin.html'
    }
@get('/signout')
def signout(requset):
    referer = requset.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_KEY,'-delete-',max_age=0,httponly=True)
    logging.info('user signed out.')
    return

@get('/manage/')
def manage():
    return 'redirect:/manage/comments'

@get('/manage/comments')
def manage_comments(*,page = '1'):
    return {
        '__template__':'manage_comments.html',
        'page_index':get_page_index(page)
    }

@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__':'manage_blog_edit.html',
        'id':'',
        'action':'/api/blogs'
    }

@get('/manage/blogs')
def manager_blogs(*,page = '1'):
    return {
        '__template__':'manage_blogs.html',
        'page_index':get_page_index(page)
    }

@get('/manage/blogs/edit')
def manage_blogs_edit(*,id):
    return {
        '__template__': 'manage_blogs.html',
        'id':id,
        'action':'/api/blogs/%s' % id
    }

@get('/manage/users')
def manage_users(*,page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index':get_page_index(page)
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
    user = yield from User.find(id)
    return user


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


@post('/api/authenticate')
def authenticate(*,email,passwd):
    if not email:
        raise APIValueError('email','Invalid email')
    if not passwd:
        raise APIValueError('passwd','Invalid passwd')
    users = yield from User.findAll('email=?',[email])
    if len(users)==0:
        raise APIValueError('email','Email not exist.')
    user = users[0]
    #check passwd
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd!= sha1.hexdigest():
        raise APIValueError('password','Invalid password')

    r = web.Response()
    #TODO:setcookie
    r.set_cookie(COOKIE_KEY,user2cookie(user,86400),max_age=86400,httponly=True)

    user.passwd = '******'
    r.content_type = 'application/json'
    r.body =json.dumps(user,ensure_ascii=False).encode('utf-8')
    return r



#blogs
@get('/api/blogs')
def api_blogs(*,page='1'):
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    p = Page(num,page_index)
    if num == 0:
        return dict(page=p,blogs = ())
    blogs = yield from Blog.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    return dict(page = p,blogs=blogs)

@get('/api/blogs/{id}')
def api_get_blog(*,id):
    blog = Blog.find(id)
    return blog

@post('/api/blogs')
def api_create_blog(request,*,name,summary,content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name','name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary','summary cannot be empty.')
    if not  content or not content.strip():
        raise APIValueError('conten','content cannot be empty.')
    blog = Blog(user_id = request.__user__.id,user_name = request.__user__.name,user_image=request.__user__.image,name =name.strip(),content=content.strip(),summary = summary.strip())
    yield from blog.save()
    return blog
@post('/api/blogs/remove')
def api_remove_blog(request,*,blog_id):
    check_admin(request)
    if not blog_id or not blog_id.strip():
        raise APIValueError('blog_id','blog_id cannot be empty.')


@get('/api/comments')
def api_comments(*,page='1'):
    page_index  = get_page_index(page)
    num = yield from Comment.findNumber('count(id)')
    p = Page(num,page_index)
    if num == 0 :
        return dict(page=p,comments = ())
    comments = yield from Comment.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    return dict(page=p,comments=comments)

@post('/api/blogs/{id}/comments')
def api_create_comment(id,request,*,content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('please signin first...')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = yield from Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment  = Comment(blog_id = blog.id ,user_id = user.id,user_name=user.name,user_image = user.image,content = content.strip())
    yield from comment.save()
    return comment

@post('/api/comments/{id}/delete')
def api_delete_comments(id,request):
    check_admin(request)
    c = yield from Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    yield from c.remove()
    return dict(id = id)


