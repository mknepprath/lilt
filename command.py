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
            quantity = None
            if c == 'all': # or check if it can be converted to a valid int
                quantity = 'all'
                b = cleanstr(d)
            elif cansplit(b) and ((c == 'the') or (c == 'a') or (c == 'an') or (c == 'some')):
                b = cleanstr(d)
            else:
                b = cleanstr(b)
            if db.select('name', 'items', 'name', b, quantity) != None:
                return (True, item.drop(b, inventory, id))
        elif (a == 'give') and c: # c must exist for give to work
            if cansplit(d) and ((e == 'the') or (e == 'a') or (e == 'an') or (e == 'some')):
                d = cleanstr(f)
            else:
                d = cleanstr(d)
            if db.select('name', 'items', 'name', d) != None:
                return (True, item.give(d, inventory, id, position, cleanstr(c)))
        elif (a == 'inventory') or (a == 'check inventory') or (a == 'what am i holding'):
            if inventory == {}:
                return (True, 'Your inventory is empty at the moment.')
            else:
                return (True, invbuild(inventory))
        elif (a == 'delete me from lilt') or (a == u'💀💀💀'):
            db.delete('users', 'id', id)
            return (True, 'You\'ve been removed from Lilt. Thanks for playing!')
        elif (a == 'liltadd') and ((id == '15332057') or (id == '724754312757272576') or (id == '15332062')):
            if len((b).split('~')) >= 2:
                addmove, addresponse = (b).split('~',1)
                if addmove == 'item':
                    # liltadd item~n|paste~m|10
                    traits = dict(trait.split('|') for trait in (addresponse).split('~'))
                    for trait in traits: # update shorthand keys
                        if trait == 'n':
                            traits['name'] = traits['n']
                            del traits['n']
                        if trait == 'm':
                            traits['max'] = traits['m']
                            del traits['m']
                    db.newitem(traits)
                    return (True, traits['name'].capitalize() + ' was added to Lilt.')
                else:
                    # liltadd throw paste at liltbird~It splatters across the window.~c|paste^inventory~d|paste
                    if len((addresponse).split('~')) >= 2:
                        addresponse, t = (addresponse).split('~',1)
                        traits = dict(trait.split('|') for trait in (t).split('~'))
                        for trait in traits: # update shorthand keys
                            if trait == 'i':
                                traits['item'] = traits['i']
                                del traits['i']
                            if trait == 'd':
                                traits['drop'] = traits['d']
                                del traits['d']
                            if trait == 'c':
                                traits['condition'] = traits['c']
                                del traits['c']
                            if trait == 't':
                                traits['trigger'] = traits['t']
                                del traits['t']
                            if trait == 'tr':
                                traits['travel'] = traits['tr']
                                del traits['tr']
                        for trait in traits: # convert condition/trigger to dicts
                            if len((traits[trait]).split('^')) >= 2:
                                traits[trait] = dict(t.split('^') for t in (traits[trait]).split('~'))
                    else:
                        traits = None
                    db.newmove(addmove, addresponse, position, traits)
                    return (True, '\'' + addmove + '\' was added to Lilt.')
    return (False, '')
