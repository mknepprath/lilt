import string
import item
from db import select, delete, newmove
from utils import cleanstr, invbuild

def get(tweet):
    if len((tweet).split()) >= 2:
        a, b = (tweet).split(' ',1)
        a = ''.join(ch for ch in a if ch not in set(string.punctuation)).lower()
        if (a == 'drop'):
            if select('name', 'items', 'name', cleanstr(b)) != None:
                return a
        elif (a == 'give'):
            c, d = (b).split(' ',1)
            e, f = (d).split(' ',1)
            if (e = 'the') or (e = 'a') or (e = 'an'):
                d = cleanstr(f)
            else:
                d = cleanstr(d)
            if select('name', 'items', 'name', d) != None:
                return a
        elif (a == 'liltadd') and ((user['id'] == '15332057') or (user['id'] == '724754312757272576')):
            return a
        else:
            return None
    else:
        return None
def drop(tweet, inventory, id):
    item_to_drop = (tweet).split(' ',1)[1]
    return item.drop(cleanstr(item_to_drop), inventory, id)
def give(tweet, inventory, id, position):
    b = (tweet).split(' ',1)[1]
    c, d = (b).split(' ',1)
    e, f = (d).split(' ',1)
    if (e = 'the') or (e = 'a') or (e = 'an'):
        item_to_give = cleanstr(f)
    else:
        item_to_give = cleanstr(d)
    return item.give(item_to_give, inventory, id, position, ''.join(ch for ch in c if ch not in set(string.punctuation)).lower())
def inventory(inventory):
    if inventory == {}:
        return 'Your inventory is empty at the moment.'
    else:
        return invbuild(inventory)
def deleteme(id):
    delete('users', 'id', id)
    return 'You\'ve been removed from Lilt. Thanks for playing!'
def liltadd(tweet, position):
    b = (tweet).split(' ',1)[1]
    addmove, addresponse = (b).split('~',1)
    newmove(addmove, addresponse, position)
    return '\'' + addmove + '\' was added to Lilt.'
