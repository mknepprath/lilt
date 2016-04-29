import json
from db import dbselect, dbupdate, log
from utils import mbuild, invbuild

def get(item, inventory, user_id, response):
    if item not in inventory:
        inventory[item] = {}
        inventory[item]['quantity'] = 1
        if len(mbuild('x'*15, invbuild(inventory))) >= 140:
            return 'Your inventory is full.'
        else:
            dbupdate(inventory, user_id)
            return response
    else:
        item_max = dbselect('max', 'items', 'name', item)
        if inventory[item]['quantity'] < item_max:
            inventory[item]['quantity'] += 1
            if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                return 'Your inventory is full.'
            else:
                dbupdate(inventory, user_id)
                return response
        else:
            return 'You can\'t hold more ' + item + '!'
def drop(drop, inventory, user_id, response=None):
    if drop not in inventory:
        if response == None:
            return 'You don\'t have anything like that.'
        else:
            return 'You don\'t have the required item, ' + drop + '.'
    elif inventory[drop]['quantity'] <= 1:
        del inventory[drop]
        dbupdate(inventory, user_id)
        if response == None:
            return 'You drop one ' + drop + '.'
        else:
            return response
    else:
        inventory[drop]['quantity'] -= 1
        dbupdate(inventory, user_id)
        if response == None:
            return 'You drop one ' + drop + '.'
        else:
            return response
def give(item, inventory, user_id, position, recipient):
    if item not in inventory:
        return 'You don\'t have ' + item + '!'
    else:
        givable = dbselect('give', 'items', 'name', item)
        if givable == False:
            return item.capitalize() + ' can\'t be given.'
        else:
            recipient_id = dbselect('id', 'users', 'name', recipient)
            if recipient_id == None:
                return 'They aren\'t playing Lilt!'
            else:
                recipient_position = dbselect('position', 'users', 'id', recipient_id)
                if recipient_position != position:
                    return 'You aren\'t close enough to them to give them that!'
                else:
                    recipient_inventory = json.loads(dbselect('inventory', 'users', 'id', recipient_id))
                    if item not in recipient_inventory:
                        recipient_inventory[item] = {}
                        recipient_inventory[item]['quantity'] = 1
                        if inventory[item]['quantity'] <= 1:
                            del inventory[item]
                        else:
                            inventory[item]['quantity'] -= 1
                        if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                            return 'Their inventory is full.'
                        else:
                            dbupdate(recipient_inventory, recipient_id)
                            dbupdate(inventory, user_id)
                            return 'You gave ' + item + ' to @' + recipient + '.'
                    else:
                        #they've got the item already, so we have to make sure they can accept more
                        item_max = dbselect('max', 'items', 'name', item)
                        if recipient_inventory[item]['quantity'] < item_max:
                            recipient_inventory[item]['quantity'] += 1
                            if inventory[item]['quantity'] <= 1:
                                del inventory[item]
                            else:
                                inventory[item]['quantity'] -= 1
                            if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                                return 'Their inventory is full.'
                            else:
                                dbupdate(recipient_inventory, recipient_id)
                                dbupdate(inventory, user_id)
                                return 'You gave ' + item + ' to @' + recipient + '.'
                        else:
                            return 'They can\'t hold more ' + item + '!'
def replace(item, drop, inventory, user_id, response):
    if inventory[drop]['quantity'] <= 1:
        if item not in inventory:
            inventory[item] = {}
            inventory[item]['quantity'] = 1
            if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                return 'Your inventory is full.'
            else:
                del inventory[drop]
                dbupdate(inventory, user_id)
                return response
        else:
            item_max = dbselect('max', 'items', 'name', item)
            if inventory[item]['quantity'] < item_max:
                inventory[item]['quantity'] += 1
                if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                    return 'Your inventory is full.'
                else:
                    del inventory[drop]
                    dbupdate(inventory, user_id)
                    return response
            else:
                return 'You can\'t hold more ' + item + '!'
    else:
        if item not in inventory:
            inventory[item] = {}
            inventory[item]['quantity'] = 1
            if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                return 'Your inventory is full.'
            else:
                inventory[drop]['quantity'] -= 1
                dbupdate(inventory, user_id)
                return response
        else:
            item_max = dbselect('max', 'items', 'name', item)
            if inventory[item]['quantity'] < item_max:
                inventory[item]['quantity'] += 1
                if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                    return 'Your inventory is full.'
                else:
                    inventory[drop]['quantity'] -= 1
                    dbupdate(inventory, user_id)
                    return response
            else:
                return 'You can\'t hold more ' + item + '!'
