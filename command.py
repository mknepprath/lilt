# -*- coding: utf-8 -*-
import string
import item
import db
from utils import cleanstr, invbuild, cansplit

def get(tweet, inventory, id, position): # drop banana # drop bologna # drop 5720 ghao
    if cansplit(tweet):
        a, b = (tweet).split(' ',1)
        a = cleanstr(a)
        if (a == 'drop'):
            if cansplit(b): #removes article
                c, d = (b).split(' ',1)
                if (c == 'the') or (c == 'a') or (c == 'an') or (c == 'some'):
                    item = cleanstr(d)
                else:
                    item = cleanstr(b)
            else:
                item = cleanstr(b)
            if db.select('name', 'items', 'name', item) != None:
                return item.drop(item, inventory, id)
        elif (a == 'give'):
            if cansplit(b):
                c, d = (b).split(' ',1)
                if cansplit(d):
                    if (e == 'the') or (e == 'a') or (e == 'an') or (e == 'some'):
                        item = cleanstr(f)
                    else:
                        item = cleanstr(d)
                else:
                    item = cleanstr(d)
                if db.select('name', 'items', 'name', item) != None:
                    return item.give(item, inventory, id, position, cleanstr(c))
        elif (a == 'inventory') or (a == 'check inventory') or (a == 'what am i holding'):
            if inventory == {}:
                return 'Your inventory is empty at the moment.'
            else:
                return invbuild(inventory)
        elif (a == 'delete me from lilt') or (a == u'💀💀💀'):
            db.delete('users', 'id', id)
            return 'You\'ve been removed from Lilt. Thanks for playing!'
        elif (a == 'liltadd') and ((id == '15332057') or (id == '724754312757272576')):
            addmove, addresponse = (b).split('~',1)
            db.newmove(addmove, addresponse, position)
            return '\'' + addmove + '\' was added to Lilt.'
    return False
