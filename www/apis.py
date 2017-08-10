#@author: ziven.mac 
#@contact: xiangzuowei@gomeplus.com.cn
#@site: www.gomeple.com
#@version: 1.0
#@license: Apache Licence
#@file: apis.py
#@time: 2017/8/7 14:50


import json,logging,inspect,functools

class APIError(Exception):
    '''
    the base APIError which contains error(required),data(optional) and message(optional).
    '''
    def __init__(self,error,data='',message=''):
        super(APIError,self).__init__(message)
        self.error=error
        self.data = data
        self.message = message

class APIValueError(APIError):
    '''
    indicate the input value has error or invalid. the data specifies the error field of input form.
    '''
    def __init__(self,field,message=''):
        super(APIValueError,self).__init__('value:invalid',field,message)
class APIResourceNotFoundError(APIError):
    '''
    indicate the resource was not found.thedata specifies the resource name.
    '''
    def __init__(self,field,message=''):
        super(APIResourceNotFoundError,self).__init__('value:notfound',field,message)

class APIPermissionError(APIError):
    '''
    indicate the api has not permission.
    '''
    def __init__(self,message=''):
        super(APIPermissionError,self).__init__('permission:forbidden',message)

