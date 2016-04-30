# -*- coding: utf-8 -*-
import string
import item
import db
from utils import cleanstr, invbuild

def get(tweet, inventory, id, position):
    if len((tweet).split()) >= 2:
        a, b = (tweet).split(' ',1)
        a = cleanstr(a)
        if (a == 'drop'):
            if len((b).split()) >= 2:
                c, d = (b).split(' ',1)
                if (c == 'the') or (c == 'a') or (c == 'an'):
                    b = cleanstr(d)
            else:
                b = cleanstr(b)
            if db.select('name', 'items', 'name', b) != None:
                return item.drop(cleanstr(b), inventory, id)
        elif (a == 'give'):
            if len((b).split()) >= 2:
                c, d = (b).split(' ',1)
                if len((d).split()) >= 2:
                    e, f = (d).split(' ',1)
                    if (e == 'the') or (e == 'a') or (e == 'an'):
                        d = cleanstr(f)
                else:
                    d = cleanstr(d)
                if db.select('name', 'items', 'name', d) != None:
                    return item.give(d, inventory, id, position, cleanstr(c))
        elif (a == 'inventory') or (a == 'check inventory') or (a == 'what am i holding'):
            if inventory == {}:
                return 'Your inventory is empty at the moment.'
            else:
                return invbuild(inventory)
        elif (a == 'delete me from lilt') or (a == u'💀💀💀'):
            db.delete('users', 'id', id)
            return 'You\'ve been removed from Lilt. Thanks for playing!'
        elif (a == 'liltadd') and ((user['id'] == '15332057') or (user['id'] == '724754312757272576')):
            addmove, addresponse = (b).split('~',1)
            db.newmove(addmove, addresponse, position)
            return '\'' + addmove + '\' was added to Lilt.'
    else:
        return False
