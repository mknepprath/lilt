# -*- coding: utf-8 -*-
import string
import re
import item
import db
from utils import cleanstr, invbuild, cansplit

def get(tweet, inventory, id, position):
    cmd = cleanstr(tweet)
    print cmd
    rend = re.sub(r'http\S+', '', tweet).lower().split() # test regex by including a link in tweet # remove articles?
    print rend
    if (rend[0] == 'drop') and (len(rend) >= 2): # drop(0) banana(1) # drop(0) the(1) dawn(2) porter(3)
        quantity = None
        if (len(rend) >= 3) and (rend[1] == 'all'): # or check if it can be converted to a valid int
            quantity = 'all'
            item = cleanstr(' '.join(rend[2:len(rend)]))
        elif (len(rend) >= 3) and ((rend[1] == 'the') or (rend[1] == 'a') or (rend[1] == 'an') or (rend[1] == 'some')):
            item = cleanstr(' '.join(rend[2:len(rend)]))
            print item
        else:
            item = cleanstr(' '.join(rend[1:len(rend)]))
        if db.select('name', 'items', 'name', item) != None:
            return (True, item.drop(item, inventory, id, quantity=quantity))
    elif (rend[0] == 'give') and (len(rend) >= 3): # give(0) @benlundsten(1) the(2) dawn(3) porter()
        if (len(rend) >= 4) and ((rend[2] == 'the') or (rend[2] == 'a') or (rend[2] == 'an') or (rend[2] == 'some')):
            item = cleanstr(' '.join(rend[3:len(rend)]))
        else:
            item = cleanstr(' '.join(rend[2:len(rend)]))
        if db.select('name', 'items', 'name', item) != None:
            return (True, item.give(item, inventory, id, position, cleanstr(rend[1])))
    elif (rend[0] == 'inventory') or (cmd == 'check inventory') or (cmd == 'what am i holding'):
        if inventory == {}:
            return (True, 'Your inventory is empty at the moment.')
        else:
            return (True, invbuild(inventory))
    elif (cmd == 'delete me from lilt') or (rend[0] == u'💀💀💀'):
        db.delete('users', 'id', id)
        return (True, 'You\'ve been removed from Lilt. Thanks for playing!')
    elif ((rend[0] == 'liltadd') or (rend[0] == 'la')) and ((id == '15332057') or (id == '724754312757272576') or (id == '15332062')):
        dbrend = str(' '.join(rend[1:len(rend)])).split('~')
        print dbrend
        if len(dbrend) >= 2:
            if dbrend[0] == 'item':
                # liltadd item~n|paste~m|10
                traits = dict(trait.split('|') for trait in dbrend[1:len(dbrend)])
                for trait in traits:
                    if trait == 'n':
                        traits['name'] = traits['n']
                        del traits['n']
                    if trait == 'm':
                        traits['max'] = traits['m']
                        del traits['m']
                db.newitem(traits)
                return (True, traits['name'].capitalize() + ' was added to Lilt.')
            elif dbrend[0] == 'copy':
                if len(dbrend) == 3:
                    db.copymove(dbrend[1], dbrend[2], position)
                    return (True, '\'' + dbrend[1] + '\' was added to Lilt as a copy of \'' + dbrend[2] + '\'.')
            else:
                # liltadd throw paste at liltbird~It splatters across the window.~c|paste^inventory~d|paste
                if len(dbrend) >= 3:
                    traits = dict(trait.split('|') for trait in dbrend[1:len(dbrend)]) # this right?
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
                            traits[trait] = dict(t.split('^') for t in dbrend[1:len(dbrend)])
                else:
                    traits = None
                db.newmove(dbrend[0], dbrend[1], position, traits)
                return (True, '\'' + dbrend[0] + '\' was added to Lilt.')
    return (False, '')
