# -*- coding: utf-8 -*-

# External
import json

# Internal
from constants import COLOR, DEBUG
import db
from utils import build_tweet, build_inventory_tweet


def get(item, inventory, user_id, response):
    print('Getting an item.')
    # This function is used for adding an item to the player's inventory.
    if item not in inventory:
        print('The player does not yet have ' + item + '.')
        # Add the item to the player's inventory and set its quantity to 1.
        inventory[item] = {}
        inventory[item]['quantity'] = 1
    else:
        print('Player has ' + item + '. Adding another.')
        # If the new item was in the inventory already, we should check that
        # they haven't reached the maximum amount they can hold of that item.
        item_max = db.select('max', 'items', 'name', item)
        print('Player can hold ' + str(item_max) + ' of these.')

        if inventory[item]['quantity'] < item_max:
            print('Player can hold one more.')
            # The player can hold another one, add 1.
            inventory[item]['quantity'] += 1
        else:
            print('Player can\'t hold anymore.')
            return 'You can\'t hold more {item}!'.format(item=item)

    print('Let\'s see how full the player\'s inventory is.')
    # Check if the player's inventory is too full after adding the item. If
    # so, return the warning without updating the database.
    # `'x' * 15` is a placeholder for a long `screen_name`.
    if len(build_tweet('x' * 15, build_inventory_tweet(inventory))) >= 140:
        return 'Your inventory is full.'

    if DEBUG.ITEM:
        print(
            COLOR.WARNING + 'Not updating inventory while debugging.' + COLOR.END)
    else:
        print(COLOR.GREEN + 'Updating inventory.' + COLOR.END)
        # Update the database with the modified inventory.
        db.update_user(inventory, user_id)

    # Return the pass-through response.
    return response


def drop(item_to_drop, inventory, user_id, response=None, quantity=None):
    # If the user attempts to drop something they don't have...
    if item_to_drop not in inventory:
        print('Player does not have {item}.'.format(item=item_to_drop))
        return 'You don\'t have anything like that.'

    # If they are removing an item from their inventory entirely...
    if inventory[item_to_drop]['quantity'] <= 1 or quantity == 'all':
        print('Deleting all {item}s from inventory.'.format(item=item_to_drop))
        del inventory[item_to_drop]
    # Otherwise, decrease its quantity by 1.
    else:
        print('Removing one {item} from inventory.'.format(item=item_to_drop))
        inventory[item_to_drop]['quantity'] -= 1

    if DEBUG.ITEM:
        print(
            COLOR.WARNING + 'Not updating inventory while debugging.' + COLOR.END)
    else:
        print(COLOR.GREEN + 'Updating inventory.' + COLOR.END)
        # Update the database with the modified inventory.
        db.update_user(inventory, user_id)

    if response != None:
        # If there is a pass-through response, return it.
        return response
    elif quantity == 'all':
        # TODO: Poorly pluralized.
        return 'You rid yourself of {item}s.'.format(item=item_to_drop)
    else:
        # Otherwise, just one is getting deleted.
        return 'You drop one {item}.'.format(item=item_to_drop)


def give(item_to_give, inventory, user_id, position, recipient):
    print('Transferring the item.')

    # Check that the player has the item in question.
    if item_to_give not in inventory:
        return 'You don\'t have {item}!'.format(item=item_to_give)
    print('The item is in player\'s inventory.')

    # If they do, make sure it's a transferrable item. Some cannot be given.
    givable = db.select('give', 'items', 'name', item_to_give)
    if givable == False:
        return '{item} can\'t be given away.'.format(item=item_to_give.capitalize())
    print('The item can be given away.')

    # If they can, check that the recipient is also a current player.
    recipient_id = db.select('id', 'users', 'name', recipient)
    if recipient_id == None:
        return 'They aren\'t playing Lilt!'
    print('The recipient is playing Lilt.')

    # If they are, make sure they're in the same location.
    recipient_position = db.select('position', 'users', 'id', recipient_id)
    if position != recipient_position:
        return 'You aren\'t close enough to them to give them that.'
    print('The players are in the same location.')

    # If they are, get the recipients inventory.
    recipient_inventory = db.select('inventory', 'users', 'id', recipient_id)

    # Attempt to add item to recipient's inventory...
    if item_to_give not in recipient_inventory:
        print('The recipient doesn\'t have this yet.')
        # Add item to recipient's inventory...
        recipient_inventory[item_to_give] = {}
        recipient_inventory[item_to_give]['quantity'] = 1
    else:
        print('The recipient has one of these already. That\'s probably fine.')
        # They've got the item already, so we have to make sure they can accept
        # more.
        item_max = db.select('max', 'items', 'name', item_to_give)
        if recipient_inventory[item_to_give]['quantity'] < item_max:
            print('Recipient can accept another one.')
            recipient_inventory[item_to_give]['quantity'] += 1
        else:
            return 'They can\'t hold more {item}!'.format(item=item_to_give)

    # And remove from player's inventory.
    if inventory[item_to_give]['quantity'] <= 1:
        del inventory[item_to_give]
    else:
        inventory[item_to_give]['quantity'] -= 1

    # Check if the recipient's inventory is too full before saving the changes.
    if len(build_tweet('x' * 15, build_inventory_tweet(recipient_inventory))) >= 140:
        return 'Their inventory is full.'

    # Update both players' inventories.
    if DEBUG.ITEM:
        print(COLOR.WARNING + 'Not updating inventories while debugging.' + COLOR.END)
    else:
        print(COLOR.GREEN + 'Updating inventories.' + COLOR.END)
        db.update_user(recipient_inventory, recipient_id)
        db.update_user(inventory, user_id)

    return 'You gave {item} to @{screen_name}.'.format(item=item_to_give, screen_name=recipient)


def replace(prev_item, next_item, inventory, user_id, response):
    print('Replacing an item.')
    # This function is used for converting one item into another, for example
    # "coin" => "bent coin".
    if next_item not in inventory:
        print('The player does not yet have ' + next_item + '.')
        # Add the item to the player's inventory and set its quantity to 1.
        inventory[next_item] = {}
        inventory[next_item]['quantity'] = 1
    else:
        print('Player has ' + next_item + '. Adding another.')
        # If the new item was in the inventory already, we should check that
        # they haven't reached the maximum amount they can hold of that item.
        item_max = db.select('max', 'items', 'name', next_item)
        print('Player can hold ' + str(item_max) + ' of these.')

        if inventory[next_item]['quantity'] < item_max:
            print('Player can hold one more.')
            # The player can hold another one, add 1.
            inventory[next_item]['quantity'] += 1
        else:
            print('Player can\'t hold anymore.')
            return 'You can\'t hold more {item}!'.format(item=next_item)

    # If they only had one of the item being replaced, remove it.
    # TODO: get() is the same as this function except for this if/else. Can we
    # share some logic here?
    if inventory[prev_item]['quantity'] <= 1:
        print('Deleting {item} from inventory.'.format(item=prev_item))
        del inventory[prev_item]
    # Otherwise, decrease its quantity by 1.
    else:
        print('Removing a {item} from inventory.'.format(item=prev_item))
        inventory[prev_item]['quantity'] -= 1

    print('Let\'s see how full the player\'s inventory is.')

    # Check if the player's inventory is too full after adding the item. If
    # so, return the warning without updating the database.
    # `'x' * 15` is a placeholder for a long `screen_name`.
    if len(build_tweet('x' * 15, build_inventory_tweet(inventory))) >= 140:
        return 'Your inventory is full.'

    if DEBUG.ITEM:
        print(
            COLOR.WARNING + 'Not updating inventory while debugging.' + COLOR.END)
    else:
        print(COLOR.GREEN + 'Updating inventory.' + COLOR.END)
        # Update the database with the modified inventory.
        db.update_user(inventory, user_id)

    # Return the pass-through response.
    return response
