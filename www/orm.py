#@author: ziven.mac 
#@contact: xiangzuowei@gomeplus.com.cn
#@site: www.gomeple.com
#@version: 1.0
#@license: Apache Licence
#@file: orm.py
#@time: 2017/7/31 10:29

import  aiomysql
import asyncio, logging

def log(sql,args = ()):
    logging.info('SQL:%s'% sql)


@asyncio.coroutine
def create_pool(loop,**kw):
    log('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host = kw.get('host','localhost'),
        port = kw.get('port',3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset','utf8'),
        autocommit = kw.get('autocommit',True),
        maxsize = kw.get('maxsize',10),
        minsize = kw.get('minsize',1),
        loop=loop
    )


@asyncio.coroutine
def select(sql,args,size = None):
    logging.info('sql=%s,args=%s' %(sql,str(args)))
    global __pool
    with (yield  from __pool) as conn:
        cur = yield  from  conn.cursor(aiomysql.DictCursor)
        yield  from cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs = yield  from cur.fetchmany(size)
        else:
            rs = yield from  cur.fetchall()
        yield from cur.close()
        logging.info('rows returned:%s' % len(rs))
        return(rs)

@asyncio.coroutine
def execute(sql,args):
    logging.info(sql,args)
    with (yield  from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?','%s'),args)

            print(sql.replace('?','%s'))
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected

def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ','.join(L)




class Field(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s,%s:%s >' % (self.__class__.__name__,self.column_type,self.name)


class StringField(Field):
    def __init__(self,name = None,primary_key = False ,default = None ,ddl = 'varchar(100)'):
        super().__init__(name,ddl,primary_key,default)

class BooleanField(Field):
    def __init__(self,name = None,primary_key = False,default = 0):
        return super().__init__(name,'boolean',False,default)
class  IntegerField(Field):
    def __init__(self,name = None,primary_key = False,default = 0):
        return super().__init__(name,'bigint',primary_key,default)
class FloatField(Field):
    def __init__(self,name = None,primary_key = False,default = 0.0):
        return super().__init__(name,'real',primary_key,default)
class TextField(Field):
    def __init__(self,name = None,primary_key = False,default = None):
        return super().__init__(name,'text',False,default)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        #排除Model类本身
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)
        #获取table名称
        tableName = attrs.get('__table__',None) or name
        logging.info('found model:%s (table:%s)' % (name,tableName))
        #获取所有的field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k ,v in attrs.items():
            if isinstance(v,Field):
                logging.info('  found mapping: %s ==> %s' % (k,v))
                mappings[k]= v
                if v.primary_key:
                    if primaryKey:
                        raise  RuntimeError('Duplucate primary key for field :%s' % k)
                    primaryKey = k
                else:fields.append(k)

        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f:'`%s`'% f,fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields
        attrs['__select__']='select `%s`,%s from `%s`' %(primaryKey,','.join(escaped_fields),tableName)
        attrs['__insert__'] = 'INSERT INTO `%s` (%s,`%s`) VALUES (%s)' % (tableName,','.join(escaped_fields),primaryKey,create_args_string(len(escaped_fields)+1))
        attrs['__update__'] = 'UPDATE `%s` set %s WHERE  `%s`=?' %(tableName,','.join(map(lambda f:'`%s`=?' %(mappings.get(f).name or f ),fields)),primaryKey)
        attrs['__delete__'] = 'delete from `%s` WHERE `%s`=?' % (tableName,primaryKey)
        return type.__new__(cls,name,bases,attrs)



class Model(dict,metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model, self).__init__(**kw)
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s' " %item)
    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self,key):
        return getattr(self,key,None)

    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        if value is None:
            field  = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    @asyncio.coroutine
    def findAll(cls,where=None,args=None,**kwargs):
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kwargs.get('orderBy',None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kwargs.get('limit',None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit,int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit,tuple) and len(limit)==2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('invalid limit value:%s' % str(limit))
        rs = yield from select(' '.join(sql),args)

        return [cls(**r) for r in rs]


    @classmethod
    @asyncio.coroutine
    def find(cls,pk):
        'find object by primary key.'
        rs = yield from  select('%s where `%s`=?' %(cls.__select__,cls.__primary_key__),[pk],1)
        if len(rs)==0:
            return None
        return cls(**rs[0])
    @classmethod
    @asyncio.coroutine
    def findNumber(cls,selectField,where = None,args = None):
        sql = ['select %s _num_ from `%s`' %(selectField,cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = yield from select(' '.join(sql),args,1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__,args)
        logging.info('save:'+ str(rows))
        if rows != 1:
            logging.warning('failed to insert record: affected rows:%s'% rows)

    @asyncio.coroutine
    def update(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = yield  from execute(self.__update__,args)
        if rows != 1:
            logging.warning('failed to update by primary key:affected rows:%s' %rows)

    def remove(self):
        pass

# class User(Model):
#     __table__ = 'users'
#     id = IntegerField(primary_key = True)
#     name = StringField()

# user = User(id = 123,name = 'Michael')
# user.save()
# User.find('uid_0001')


