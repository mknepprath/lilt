import string
from db import dbselect
from utils import cleanstr

def drop(a, b):
    print 'in drop function'
    if dbselect('name', 'items', 'name', cleanstr(b)) != None:
        print 'returning...'
        return a
        return cleanstr(b)
    else:
        pass
def give(a, b):
    c, d = (b).split(' ',1)
    if dbselect('name', 'items', 'name', cleanstr(d)) != None:
        return a
        return ''.join(ch for ch in c if ch not in set(string.punctuation)).lower()
        return cleanstr(d)
    else:
        pass
def liltadd(a, b):
    c, d = (b).split('~',1)
    return a
    return str(c)
    return str(d)
