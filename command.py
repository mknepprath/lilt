# -*- coding: utf-8 -*-
import string
import item
import db
from utils import cleanstr, invbuild, cansplit

def get(tweet, inventory, id, position):
    if cansplit(tweet):
        a, b = (tweet).split(' ',1)
        if cansplit(b):
            c, d = (b).split(' ',1)
            if cansplit(d):
                e, f = (d).split(' ',1)
        a = cleanstr(a)
        if (a == 'drop'):
            if cansplit(b) and ((c == 'the') or (c == 'a') or (c == 'an') or (c == 'some')):
                b = cleanstr(d)
            else:
                b = cleanstr(b)
            if db.select('name', 'items', 'name', b) != None:
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
        elif (a == 'liltadd') and ((id == '15332057') or (id == '724754312757272576') or (id == '15332062')):
            # example: @familiarlilt use sword on door~You smash it open.~item|wood~trigger|door^smashed~
            addmove, addresponse = (b).split('~',1)
            if len((addresponse).split('~')) >= 2:
                addresponse, t = (addresponse).split('~',1)
                traits = dict(trait.split('|') for trait in (t).split('~'))
                for trait in traits: # trigger
                    print trait # trigger
                    print traits[trait] # door^smashed
                    if len((traits[trait]).split('^')) >= 2:
                        traits[trait] = dict(t.split('^') for t in (traits[trait]).split('~'))
                    print traits[trait]
                print traits
            else:
                pass
            # db.newmove(addmove, addresponse, position)
            return '\'' + addmove + '\' was added to Lilt.'
    return False
