# -*- coding: utf-8 -*-
import string
import item
from db import select, delete, newmove
from utils import cleanstr, invbuild

def get(tweet, inventory, id, position):
    if len((tweet).split()) >= 2:
        a, b = (tweet).split(' ',1)
        a = ''.join(ch for ch in a if ch not in set(string.punctuation)).lower()

        if (a == 'drop'):
            if select('name', 'items', 'name', cleanstr(b)) != None:
                return item.drop(cleanstr(b), inventory, id)

        elif (a == 'give'):
            c, d = (b).split(' ',1)
            e, f = (d).split(' ',1)
            if (e == 'the') or (e == 'a') or (e == 'an'):
                d = cleanstr(f)
            else:
                d = cleanstr(d)
            if select('name', 'items', 'name', d) != None:
                print 'going to return...'
                return item.give(d, inventory, id, position, ''.join(ch for ch in c if ch not in set(string.punctuation)).lower())

        elif (a == 'inventory') or (a == 'check inventory'):
            if inventory == {}:
                return 'Your inventory is empty at the moment.'
            else:
                return invbuild(inventory)

        elif (a == 'delete me from lilt') or (a == u'💀💀💀'):
            delete('users', 'id', id)
            return 'You\'ve been removed from Lilt. Thanks for playing!'

        elif (a == 'liltadd') and ((user['id'] == '15332057') or (user['id'] == '724754312757272576')):
            addmove, addresponse = (b).split('~',1)
            newmove(addmove, addresponse, position)
            return '\'' + addmove + '\' was added to Lilt.'
    else:
        return None
