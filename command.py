# -*- coding: utf-8 -*-
import string
import re
import item
import db
from utils import cleanstr, invbuild, cansplit

def get(tweet, inventory, id, position):
    rend = re.sub(r'http\S+', '', tweet).lower().split() # remove articles here?
    if (rend[0] == 'drop') and (len(rend) >= 2): # drop(0) banana(1) # drop(0) the(1) dawn(2) porter(3)
        quantity = None
        if (len(rend) >= 3) and (rend[1] == 'all'): # or check if it can be converted to a valid int
            quantity = 'all'
            drop_item = cleanstr(' '.join(rend[2:len(rend)]))
        elif (len(rend) >= 3) and ((rend[1] == 'the') or (rend[1] == 'a') or (rend[1] == 'an') or (rend[1] == 'some')):
            drop_item = cleanstr(' '.join(rend[2:len(rend)]))
        else:
            drop_item = cleanstr(' '.join(rend[1:len(rend)]))
        if db.select('name', 'items', 'name', drop_item) != None:
            return (True, item.drop(drop_item, inventory, id, quantity=quantity))
    elif (rend[0] == 'give') and (len(rend) >= 3): # give(0) @benlundsten(1) the(2) dawn(3) porter()
        if (len(rend) >= 4) and ((rend[2] == 'the') or (rend[2] == 'a') or (rend[2] == 'an') or (rend[2] == 'some')):
            give_item = cleanstr(' '.join(rend[3:len(rend)]))
        else:
            give_item = cleanstr(' '.join(rend[2:len(rend)]))
        if db.select('name', 'items', 'name', give_item) != None:
            return (True, item.give(give_item, inventory, id, position, cleanstr(rend[1])))
    elif (rend[0] == 'inventory') or (' '.join(rend) == 'check inventory') or (' '.join(rend) == 'what am i holding'):
        if inventory == {}:
            return (True, 'Your inventory is empty at the moment.')
        else:
            return (True, invbuild(inventory))
    elif (' '.join(rend) == 'delete me from lilt') or (rend[0] == u'💀💀💀'):
        db.delete('users', 'id', id)
        return (True, 'You\'ve been removed from Lilt. Thanks for playing!')
    elif ((rend[0] == 'liltadd') or (rend[0] == 'la')) and ((id == '15332057') or (id == '724754312757272576') or (id == '15332062')):
        dbrend = str(' '.join(rend[1:len(rend)])).split('~')
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
                    return (True, '\'' + dbrend[2] + '\' was added to Lilt as a copy of \'' + dbrend[1] + '\'.')
            elif dbrend[0] == 'do':
                # la do~insert~moves~move|look at cat~response|It's sassy.~c|box^open~t|cat^sighted
                # la do~update~moves~c|cat^spotted~move|look at cat~response|It's sassy.~c|box^open~t|cat^sighted
                if dbrend[1] == 'select':
                    dbval = dbrend[3]
                    data = dict(key.split('|') for key in dbrend[4:len(dbrend)])
                elif dbrend[1] == 'update':
                    dbval = dict(key.split('|') for key in dbrend[3:4])
                    data = dict(key.split('|') for key in dbrend[4:len(dbrend)])
                    for key in dbval:
                        if len((dbval[key]).split('^')) >= 2:
                            dbval[key] = dict(k.split('^') for k in (dbval[key]).split('~'))
                else: # insert/delete
                    dbval = None
                    data = dict(key.split('|') for key in dbrend[3:len(dbrend)])
                for key in data: #shorthands
                    if key == 'n':
                        data['name'] = data['n']
                        del data['n']
                    if key == 'm':
                        data['max'] = data['m']
                        del data['m']
                for key in data: # convert condition/trigger to dicts
                    if len((data[key]).split('^')) >= 2:
                        data[key] = dict(k.split('^') for k in (data[key]).split('~'))
                dbfetch = db.do(dbrend[1], dbrend[2], data, val=dbval)
                if dbrend[1] == 'insert':
                    return (True, str(data) + ' was added to ' + dbrend[2].capitalize() + '.')
                elif dbrend[1] == 'select':
                    if len(dbfetch) < 1:
                        return (True, 'Nothing was selected.')
                    elif len(dbfetch) == 1:
                        return (True, '\'' + str(dbfetch[0][0]) + '\' was fetched from ' + dbrend[2].capitalize() + '.')
                    elif len(dbfetch) == 2:
                        return (True, '\'' + str(dbfetch[0][0]) + '\' was fetched from ' + dbrend[2].capitalize() + ', along with ' + str(len(dbfetch) - 1) + ' other.')
                    else:
                        return (True, '\'' + str(dbfetch[0][0]) + '\' was fetched from ' + dbrend[2].capitalize() + ', along with ' + str(len(dbfetch) - 1) + ' others.')
                elif dbrend[1] == 'update':
                    return (True, dbrend[2].capitalize() + ' was updated with ' + str(dbval) + '.')
                elif dbrend[1] == 'delete':
                    return (True, str(data) + ' was deleted from ' + dbrend[2].capitalize() + '.')
            else: # newmove
                # la(rend[0]) eat meat cake(1)~It looks pretty nasty! But you eat it...(2)~c|meat cake^inventory(3)~d|meat cake(4)
                if len(dbrend) >= 3:
                    traits = dict(trait.split('|') for trait in dbrend[2:len(dbrend)]) # this right?
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
                db.newmove(dbrend[0], dbrend[1], position, traits)
                return (True, '\'' + dbrend[0] + '\' was added to Lilt.')
    return (False, '')
