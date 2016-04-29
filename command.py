import string
import item
from db import dbselect
from utils import cleanstr

def get(tweet):
    if len((tweet).split()) >= 2:
        a, b = (tweet).split(' ',1)
        a = ''.join(ch for ch in a if ch not in set(string.punctuation)).lower()
        if (a == 'drop'):
            if dbselect('name', 'items', 'name', cleanstr(b)) != None:
                return a
        elif (a == 'give'):
            c, d = (b).split(' ',1)
            if dbselect('name', 'items', 'name', cleanstr(d)) != None:
                return a
        elif (a == 'liltadd') and ((user['id'] == '15332057') or (user['id'] == '724754312757272576')):
            return a
        else:
            return None
    else:
        return None
def drop(tweet, inventory, id):
    item_to_drop = (tweet).split(' ',1)[1]
    return item.drop(cleanstr(item_to_drop), inventory, id))
def give(tweet, inventory, id, position):
    b = (tweet).split(' ',1)[1]
    c, d = (b).split(' ',1)
    return item.give(''.join(ch for ch in c if ch not in set(string.punctuation)).lower(), inventory, id, position, cleanstr(d))
def liltadd(tweet):
    b = (tweet).split(' ',1)[1]
    c, d = (b).split('~',1)
    return (str(c), str(d))
