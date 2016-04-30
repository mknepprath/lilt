# -*- coding: utf-8 -*-
import string
import item
import db
from utils import cleanstr, invbuild, cansplit

def get(tweet, inventory, id, position): # drop banana # drop bologna # drop 5720 ghao
    if cansplit(tweet):
        a, b = (tweet).split(' ',1)
        if cansplit(b):
            c, d = (b).split(' ',1)
        if cansplit(d):
            e, f = (d).split(' ',1)
        a = cleanstr(a)
        if (a == 'drop'):
            print '1'
            if cansplit(b) and ((c == 'the') or (c == 'a') or (c == 'an') or (c == 'some')):
                b = cleanstr(d)
            else:
                print '2'
                b = cleanstr(b)
            print '3'
            if db.select('name', 'items', 'name', b) != None:
                print '4'
                return item.drop(b, inventory, id)
        elif (a == 'give') and c: # c must exist for give to work
            if cansplit(d) and ((e == 'the') or (e == 'a') or (e == 'an') or (e == 'some')):
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
        elif (a == 'liltadd') and ((id == '15332057') or (id == '724754312757272576')):
            addmove, addresponse = (b).split('~',1)
            db.newmove(addmove, addresponse, position)
            return '\'' + addmove + '\' was added to Lilt.'
    return False
