import string

def getitem(item, inventory, user_id, response):
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
def dropitem(drop, inventory, user_id, response=None):
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
def giveitem(item, inventory, user_id, position, recipient):
    log('So you want to give ' + item + ' to ' + recipient + '.')
    if item not in inventory:
        log(item + ' wasn\'t in your inventory.')
        return 'You don\'t have ' + item + '!'
    else:
        log('Okay, so you do have the item.')
        givable = dbselect('give', 'items', 'name', item)
        log('Givableness of item should be above this...')
        if givable == False:
            log('Can\'t give that away!')
            return item.capitalize() + ' can\'t be given.'
        else:
            recipient_id = dbselect('id', 'users', 'name', recipient)
            if recipient_id == None:
                log('Yeah, that person doesn\'t exist.')
                return 'They aren\'t playing Lilt!'
            else:
                recipient_position = dbselect('position', 'users', 'id', recipient_id)
                log('Got the position for recipient, I think.')
                if recipient_position != position:
                    log('You aren\'t close enough to the recipient to give them anything.')
                    return 'You aren\'t close enough to them to give them that!'
                else:
                    recipient_inventory = json.loads(dbselect('inventory', 'users', 'id', recipient_id))
                    log('Got the recipient\'s inventory.')
                    if item not in recipient_inventory:
                        log('Oh yeah, they didn\'t have that item.')
                        recipient_inventory[item] = {}
                        recipient_inventory[item]['quantity'] = 1
                        if inventory[item]['quantity'] <= 1:
                            del inventory[item]
                        else:
                            inventory[item]['quantity'] -= 1
                        if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                            log('Hmm. Yup, they couldn\'t hold anything else.')
                            return 'Their inventory is full.'
                        else:
                            log('Alright, so they should be able to hold this item.')
                            dbupdate(recipient_inventory, recipient_id)
                            dbupdate(inventory, user_id)
                            log('Now they got it.')
                            return 'You gave ' + item + ' to @' + recipient + '.'
                    else:
                        #they've got the item already, so we have to make sure they can accept more
                        item_max = dbselect('max', 'items', 'name', item)
                        log('I think the item max has been grabbed hopefully... we\'ll see.')
                        if recipient_inventory[item]['quantity'] < item_max:
                            log('Should be room in their inventory for the item.')
                            recipient_inventory[item]['quantity'] += 1
                            if inventory[item]['quantity'] <= 1:
                                del inventory[item]
                            else:
                                inventory[item]['quantity'] -= 1
                            if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                                return 'Their inventory is full.'
                            else:
                                log('Update the database with inventory stuff, because it\'s all good.')
                                dbupdate(recipient_inventory, recipient_id)
                                dbupdate(inventory, user_id)
                                return 'You gave ' + item + ' to @' + recipient + '.'
                        else:
                            return 'They can\'t hold more ' + item + '!'
def replaceitem(item, drop, inventory, user_id, response):
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
                    log('You drop one ' + drop + ' due to a move.')
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
                    log('You drop one ' + drop + ' due to a move.')
                    return response
            else:
                return 'You can\'t hold more ' + item + '!'
def getcurrentevent(move, position, inventory, events):
    events_inv = events
    items = list(inventory.keys())
    for item in items:
        events_inv[position][item] = 'inventory'
    current_event = None
    for key, value in events_inv[position].iteritems():
        event = {}
        event[key] = value
        # check if there is a response for this move when condition is met (this event)
        response = dbselect('response', 'moves', 'move', move, position, event)
        if response != None:
            current_event = event
            break
    return current_event
def invbuild(inventory):
    items = list(inventory.keys())
    i = 0
    while i < len(items):
        iq = inventory[items[i]]['quantity'] # item quantity (items[i] would resolve to item's name)
        if iq > 1: # only append quantity info if more than one
            items[i] += ' ' + u'\u2022'*iq
        i += 1
    return ', '.join(items)
def mbuild(screen_name, message):
    return '@' + screen_name + ' ' + message
def cleanstr(s):
    s_mod = re.sub(r'http\S+', '', s) # removes links
    s_mod = re.sub(r' the ', ' ', s_mod) #remove the word "the" // probably a better solution for this...
    s_mod = re.sub(' +',' ', s_mod) # removes extra spaces
    ns = ''.join(ch for ch in s_mod if ch not in set(string.punctuation)).lower().rstrip() # removes punctuation
    return ns
