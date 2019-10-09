# -*- coding: utf-8 -*-

"""
Functions for programmatic actions that don't get responses from a database
queries. For instance, requesting an inventory status or giving another player
an item.
"""

# External
import re

# Internal
from constants import LILTBUILDER, MKNEPPRATH
import db
import item
from utils import filter_tweet, build_inventory_tweet


def get(tweet, inventory, id, position):
    # Remove articles here?
    tweet_array = re.sub(r'http\S+', '', tweet).lower().split()
    print('Scanning words:', tweet_array)

    # Drop an item.
    # - drop[0] banana[1]
    # - drop[0] the[1] dawn[2] porter[3]
    if (tweet_array[0] == 'drop') and (len(tweet_array) >= 2):
        # Initialize quantity at None.
        quantity = None

        # If the first word in the tweet is 'all', drop all of that item.
        if (len(tweet_array) >= 3) and (tweet_array[1] == 'all'):
            # Set quantity to all.
            quantity = 'all'
            # Derive item to drop from tweet array.
            drop_item = filter_tweet(' '.join(tweet_array[2:len(tweet_array)]))
        # Remove articles and derive item to drop from tweet array.
        elif (len(tweet_array) >= 3) and ((tweet_array[1] == 'the') or (tweet_array[1] == 'a') or (tweet_array[1] == 'an') or (tweet_array[1] == 'some')):
            drop_item = filter_tweet(' '.join(tweet_array[2:len(tweet_array)]))
        # Derive item to drop from tweet array.
        else:
            drop_item = filter_tweet(' '.join(tweet_array[1:len(tweet_array)]))

        # Check that the derived item exists before returning it.
        if db.select('name', 'items', 'name', drop_item) != None:
            return item.drop(drop_item, inventory, id, quantity=quantity)

    # Give another player an item.
    # - give[0] @benlundsten[1] the[2] dawn[3] porter[4]
    elif (tweet_array[0] == 'give') and (len(tweet_array) >= 3):
        # Derive item to give from tweet word array.
        if (len(tweet_array) >= 4) and ((tweet_array[2] == 'the') or (tweet_array[2] == 'a') or (tweet_array[2] == 'an') or (tweet_array[2] == 'some')):
            give_item = filter_tweet(' '.join(tweet_array[3:len(tweet_array)]))
        else:
            give_item = filter_tweet(' '.join(tweet_array[2:len(tweet_array)]))
        print('Giving ' + give_item + '.')

        # Check if the item exists.
        if db.select('name', 'items', 'name', give_item) != None:
            return (item.give(give_item, inventory, id, position, tweet_array[1][1:].lower()))

    # Inventory request.
    elif (tweet_array[0] == 'inventory') or (' '.join(tweet_array) == 'check inventory') or (' '.join(tweet_array) == 'what am i holding'):
        if inventory == {}:
            return 'Your inventory is empty at the moment.'
        else:
            return build_inventory_tweet(inventory)

    # Deletion request.
    elif (' '.join(tweet_array) == 'delete me from lilt') or (tweet_array[0] == u'💀💀💀'):
        db.delete('users', 'id', id)
        return 'You\'ve been removed from Lilt. Thanks for playing!'

    # Admin only from this point down.
    # - Add items
    # - Copy, add, or update moves
    # - Or do basically anything else with the database...
    elif (tweet_array[0] == 'liltadd' or tweet_array[0] == 'la') and (id == MKNEPPRATH or id == LILTBUILDER):
        builder_query_array = str(
            ' '.join(tweet_array[1:len(tweet_array)])).split('~')
        if len(builder_query_array) >= 2:
            if builder_query_array[0] == 'item':
                # liltadd item~n|paste~m|10
                traits = dict(trait.split('|')
                              for trait in builder_query_array[1:len(builder_query_array)])
                for trait in traits:
                    if trait == 'n':
                        traits['name'] = traits['n']
                        del traits['n']
                    if trait == 'm':
                        traits['max'] = traits['m']
                        del traits['m']
                db.new_item(traits)
                return traits['name'].capitalize() + ' was added to Lilt.'
            elif builder_query_array[0] == 'copy':
                if len(builder_query_array) == 3:
                    db.copy_move(
                        builder_query_array[1], builder_query_array[2], position)
                    return '\'' + builder_query_array[2] + '\' was added to Lilt as a copy of \'' + builder_query_array[1] + '\'.'
            elif builder_query_array[0] == 'do':
                # la do~insert~moves~move|look at cat~response|It's sassy.~c|box^open~t|cat^sighted
                # la do~update~moves~c|cat^spotted~move|look at cat~response|It's sassy.~c|box^open~t|cat^sighted
                if builder_query_array[1] == 'select':
                    dbval = builder_query_array[3]
                    data = dict(key.split('|')
                                for key in builder_query_array[4:len(builder_query_array)])
                elif builder_query_array[1] == 'update':
                    dbval = dict(key.split('|')
                                 for key in builder_query_array[3:4])
                    data = dict(key.split('|')
                                for key in builder_query_array[4:len(builder_query_array)])
                    for key in dbval:
                        if len((dbval[key]).split('^')) >= 2:
                            dbval[key] = dict(k.split('^')
                                              for k in (dbval[key]).split('~'))
                else:  # insert/delete
                    dbval = None
                    data = dict(key.split('|')
                                for key in builder_query_array[3:len(builder_query_array)])
                for key in data:  # shorthands
                    if key == 'n':
                        data['name'] = data['n']
                        del data['n']
                    if key == 'mx':
                        data['max'] = data['mx']
                        del data['mx']
                    if key == 'm':
                        data['move'] = data['m']
                        del data['m']
                    if key == 'p':
                        data['position'] = data['p']
                        del data['p']
                    if key == 'i':
                        data['item'] = data['i']
                        del data['i']
                    if key == 'd':
                        data['drop'] = data['d']
                        del data['d']
                    if key == 'c':
                        data['condition'] = data['c']
                        del data['c']
                    if key == 't':
                        data['trigger'] = data['t']
                        del data['t']
                    if key == 'tr':
                        data['travel'] = data['tr']
                        del data['tr']
                for key in data:  # convert condition/trigger to dicts
                    if len((data[key]).split('^')) >= 2:
                        data[key] = dict(k.split('^')
                                         for k in (data[key]).split('~'))
                dbfetch = db.do(
                    builder_query_array[1], builder_query_array[2], data, val=dbval)
                if builder_query_array[1] == 'insert':
                    if builder_query_array[2] == 'moves':
                        return '\'' + str(data['move']) + '\' was added to ' + builder_query_array[2].capitalize() + '.'
                    elif builder_query_array[2] == 'items':
                        return '\'' + str(data['name']) + '\' was added to ' + builder_query_array[2].capitalize() + '.'
                    else:
                        return 'That was added to ' + builder_query_array[2].capitalize() + '.'
                elif builder_query_array[1] == 'select':
                    if len(dbfetch) < 1:
                        return 'Nothing was selected from ' + str(dbval) + '.'
                    elif len(dbfetch) == 1:
                        return '\'' + str(dbfetch[0][0]) + '\' was fetched from ' + str(dbval) + ' in ' + builder_query_array[2].capitalize() + '.'
                    elif len(dbfetch) == 2:
                        return '\'' + str(dbfetch[0][0]) + '\' was fetched from ' + str(dbval) + ' in ' + builder_query_array[2].capitalize() + ', along with ' + str(len(dbfetch) - 1) + ' other.'
                    else:
                        return '\'' + str(dbfetch[0][0]) + '\' was fetched from ' + str(dbval) + ' in ' + builder_query_array[2].capitalize() + ', along with ' + str(len(dbfetch) - 1) + ' others.'
                elif builder_query_array[1] == 'update':
                    return builder_query_array[2].capitalize() + ' was updated with ' + str(dbval) + '.'
                elif builder_query_array[1] == 'delete':
                    return '\'' + str(data) + '\' was deleted from ' + builder_query_array[2].capitalize() + '.'
            else:  # new_move
                # la(tweet_array[0]) eat meat cake(1)~It looks pretty nasty! But you eat it...(2)~c|meat cake^inventory(3)~d|meat cake(4)
                if len(builder_query_array) >= 3:
                    traits = dict(trait.split('|')
                                  for trait in builder_query_array[2:len(builder_query_array)])  # this right?
                    for trait in traits:  # update shorthand keys
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
                    for trait in traits:  # convert condition/trigger to dicts
                        if len((traits[trait]).split('^')) >= 2:
                            traits[trait] = dict(t.split('^')
                                                 for t in (traits[trait]).split('~'))
                else:
                    traits = None
                db.new_move(
                    builder_query_array[0], builder_query_array[1], position, traits)
                return ('\'' + builder_query_array[0] + '\' was added to Lilt.')
    return ''
