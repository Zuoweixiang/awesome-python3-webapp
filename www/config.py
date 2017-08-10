#@author: ziven.mac
#@contact: xiangzuowei@gomeplus.com.cn
#@site: www.gomeple.com
#@version: 1.0
#@license: Apache Licence
#@file: app.py
#@time: 2017/7/25 15:08

import config_default

class Dict(dict):
    def __init__(self,names=(),values=(),**kwargs):
        super(Dict,self).__init__(**kwargs)
        for k,v in zip(names,values):
            self[k] = v

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" %item)


    def __setattr__(self, key, value):
        self[key]=value

def merge(defaults,override):
    r = {}
    for k,v in defaults.items():
        if k in override:
            if isinstance(v,dict):
                r[k]= merge(v,override[k])
            else:
                r[k]=override[k]
        else:
            r[k]= v

    return r
def toDict(d):
    D = Dict()
    for k,v in d.items():
        D[k]= toDict(v) if isinstance(v,dict) else v
    return D

configs = config_default.configs

try:
    import  config_override
    configs = merge(configs,config_override.configs)
except ImportError:
    pass

configs = toDict(configs)








