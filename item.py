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
    log(rec, 'So you want to give ' + item + ' to ' + recipient + '.')
    if item not in inventory:
        log(rec, item + ' wasn\'t in your inventory.')
        return 'You don\'t have ' + item + '!'
    else:
        log(rec, 'Okay, so you do have the item.')
        givable = dbselect('give', 'items', 'name', item)
        log(rec, 'Givableness of item should be above this...')
        if givable == False:
            log(rec, 'Can\'t give that away!')
            return item.capitalize() + ' can\'t be given.'
        else:
            recipient_id = dbselect('id', 'users', 'name', recipient)
            if recipient_id == None:
                log(rec, 'Yeah, that person doesn\'t exist.')
                return 'They aren\'t playing Lilt!'
            else:
                recipient_position = dbselect('position', 'users', 'id', recipient_id)
                log(rec, 'Got the position for recipient, I think.')
                if recipient_position != position:
                    log(rec, 'You aren\'t close enough to the recipient to give them anything.')
                    return 'You aren\'t close enough to them to give them that!'
                else:
                    recipient_inventory = json.loads(dbselect('inventory', 'users', 'id', recipient_id))
                    log(rec, 'Got the recipient\'s inventory.')
                    if item not in recipient_inventory:
                        log(rec, 'Oh yeah, they didn\'t have that item.')
                        recipient_inventory[item] = {}
                        recipient_inventory[item]['quantity'] = 1
                        if inventory[item]['quantity'] <= 1:
                            del inventory[item]
                        else:
                            inventory[item]['quantity'] -= 1
                        if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                            log(rec, 'Hmm. Yup, they couldn\'t hold anything else.')
                            return 'Their inventory is full.'
                        else:
                            log(rec, 'Alright, so they should be able to hold this item.')
                            dbupdate(recipient_inventory, recipient_id)
                            dbupdate(inventory, user_id)
                            log(rec, 'Now they got it.')
                            return 'You gave ' + item + ' to @' + recipient + '.'
                    else:
                        #they've got the item already, so we have to make sure they can accept more
                        item_max = dbselect('max', 'items', 'name', item)
                        log(rec, 'I think the item max has been grabbed hopefully... we\'ll see.')
                        if recipient_inventory[item]['quantity'] < item_max:
                            log(rec, 'Should be room in their inventory for the item.')
                            recipient_inventory[item]['quantity'] += 1
                            if inventory[item]['quantity'] <= 1:
                                del inventory[item]
                            else:
                                inventory[item]['quantity'] -= 1
                            if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                                return 'Their inventory is full.'
                            else:
                                log(rec, 'Update the database with inventory stuff, because it\'s all good.')
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
            # check if there's room in the inventory
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
                # check if there's room in the inventory
                if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                    return 'Your inventory is full.'
                else:
                    del inventory[drop]
                    dbupdate(inventory, user_id)
                    log(rec, 'You drop one ' + drop + ' due to a move.')
                    return response
            else:
                return 'You can\'t hold more ' + item + '!'
    else:
        if item not in inventory:
            inventory[item] = {}
            inventory[item]['quantity'] = 1
            # check if there's room in the inventory
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
                # check if there's room in the inventory
                if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                    return 'Your inventory is full.'
                else:
                    inventory[drop]['quantity'] -= 1
                    dbupdate(inventory, user_id)
                    log(rec, 'You drop one ' + drop + ' due to a move.')
                    return response
            else:
                return 'You can\'t hold more ' + item + '!'
