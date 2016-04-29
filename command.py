import string
from db import dbselect
from utils import cleanstr

def get(tweet):
    print '1'
    if len((tweet).split()) >= 2:
        a = (tweet).split(' ',1)[0]
        a = ''.join(ch for ch in a if ch not in set(string.punctuation)).lower()
        if (a == 'drop'):
            if dbselect('name', 'items', 'name', cleanstr(b)) != None:
                return a
        elif (a == 'give'):
            print '2'
            c, d = (b).split(' ',1)
            print '3'
            if dbselect('name', 'items', 'name', cleanstr(d)) != None:
                print '4'
                return a
        elif (a == 'liltadd') and ((user['id'] == '15332057') or (user['id'] == '724754312757272576')):
            return a
        else:
            return None
    else:
        return None
def drop(tweet):
    b = (tweet).split(' ',1)[1]
    return (cleanstr(b))
def give(tweet):
    b = (tweet).split(' ',1)[1]
    c, d = (b).split(' ',1)
    return (''.join(ch for ch in c if ch not in set(string.punctuation)).lower(), cleanstr(d))
def liltadd(tweet):
    b = (tweet).split(' ',1)[1]
    c, d = (b).split('~',1)
    return (str(c), str(d))
