# -*- coding: utf-8 -*-
import os
import time
import string
import random
import tweepy
import psycopg2
import urlparse
import json
import re

# debugging options
debug = True

# init postgresql database
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cur = conn.cursor()

class TwitterAPI:
    """
    Class for accessing the Twitter API.

    Requires API credentials to be available in environment
    variables. These will be set appropriately if the bot was created
    with init.sh included with the heroku-twitterbot-starter
    """
    def __init__(self):
        consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
        consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def tweet(self, message):
        """Send a tweet"""
        self.api.update_status(status=message)

    def reply(self, message, tweet_id):
        """Reply to a tweet"""
        self.api.update_status(status=message, in_reply_to_status_id=tweet_id)

def item(item, inventory, user_id, response=None):
    print "item management"
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
    print 'So you want to give ' + item + ' to ' + recipient + '.'
    if item not in inventory:
        print item + ' wasn\'t in your inventory.' #TESTING
        return 'You don\'t have ' + item + '!'
    else:
        print 'Okay, so you do have the item.' #TESTING
        givable = dbselect('give', 'items', 'name', item)
        print 'Givableness of item should be above this...'
        if givable == False:
            print 'Can\'t give that away!'
            return item.capitalize() + ' can\'t be given.'
        else:
            recipient_id = dbselect('id', 'users', 'name', recipient)
            if recipient_id == None:
                print 'Yeah, that person doesn\'t exist.' #TESTING
                return 'They aren\'t playing Lilt!'
            else:
                recipient_position = dbselect('position', 'users', 'id', recipient_id)
                print 'Got the position for recipient, I think.' #TESTING
                if recipient_position != position:
                    print 'You aren\'t close enough to the recipient to give them anything.' #TESTING
                    return 'You aren\'t close enough to them to give them that!'
                else:
                    recipient_inventory = json.loads(dbselect('inventory', 'users', 'id', recipient_id))
                    print 'Got the recipient\'s inventory.' #TESTING
                    if item not in recipient_inventory:
                        print 'Oh yeah, they didn\'t have that item.'
                        recipient_inventory[item] = {}
                        recipient_inventory[item]['quantity'] = 1
                        if inventory[item]['quantity'] <= 1:
                            del inventory[item]
                        else:
                            inventory[item]['quantity'] -= 1
                        if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                            print 'Hmm. Yup, they couldn\'t hold anything else.' #TESTING
                            return 'Their inventory is full.'
                        else:
                            print 'Alright, so they should be able to hold this item.' #TESTING
                            dbupdate(recipient_inventory, recipient_id)
                            dbupdate(inventory, user_id)
                            print 'Now they got it.' #TESTING
                            return 'You gave ' + item + ' to @' + recipient + '.'
                    else:
                        #they've got the item already, so we have to make sure they can accept more
                        item_max = dbselect('max', 'items', 'name', item)
                        print 'I think the item max has been grabbed hopefully... we\'ll see.' #TESTING
                        if recipient_inventory[item]['quantity'] < item_max:
                            print 'Should be room in their inventory for the item.' #TESTING
                            recipient_inventory[item]['quantity'] += 1
                            if inventory[item]['quantity'] <= 1:
                                del inventory[item]
                            else:
                                inventory[item]['quantity'] -= 1
                            if len(mbuild('x'*15, invbuild(recipient_inventory))) >= 140:
                                return 'Their inventory is full.'
                            else:
                                print 'Update the database with inventory stuff, because it\'s all good.' #TESTING
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
                    print 'You drop one ' + drop + ' due to a move.'
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
                    print 'You drop one ' + drop + ' due to a move.'
                    return response
            else:
                return 'You can\'t hold more ' + item + '!'
def invbuild(inventory):
    items = list(inventory.keys())
    i = 0
    while i < len(items):
        iq = inventory[items[i]]['quantity'] # item quantity (items[i] would resolve to item's name)
        if iq > 1: # only append quantity info if more than one
            items[i] += ' ' + u'\u2022'*iq
        i += 1
    return ', '.join(items)
def storeerror(move, position):
    attempt = dbselect('attempts', 'attempts', 'move', move, position)
    if attempt == None:
        cur.execute("INSERT INTO attempts (move, position, attempts) VALUES (%s, %s, %s)", (str(move),str(position),1))
        conn.commit()
    else:
        dbupdate(attempt+1, move, 'attempts')
    return "Stored the failed attempt for future reference."
def dbselect(col1, table, col2, val, position=None, condition=None):
    if condition != None:
        cur.execute("SELECT " + col1 + " FROM " + table + " WHERE move = %s AND position = %s AND condition = %s;", (val,position,json.dumps(condition)))
    elif position != None:
        cur.execute("SELECT " + col1 + " FROM " + table + " WHERE move = %s AND position = %s AND condition IS NULL;", (val,position))
    else:
        cur.execute("SELECT " + col1 + " FROM " + table + " WHERE " + col2 + " = %s;", (val,))
    o = cur.fetchone()
    if o == None:
        return o
    else:
        return o[0]
def dbupdate(val1, val2, col='inventory'):
    if (col != 'inventory') and (col != 'events') and (col != 'attempts'):
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (val1, val2))
    elif col == 'attempts':
        cur.execute("UPDATE attempts SET " + col + " = %s WHERE move = %s", (val1, val2))
    else:
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (json.dumps(val1), val2))
    conn.commit()
def cleanstr(s):
    s_mod = re.sub(r'http\S+', '', s) # removes links
    s_mod = re.sub(' +',' ', s_mod) # removes extra spaces
    ns = ''.join(ch for ch in s_mod if ch not in exclude).lower().rstrip() # removes punctuation
    return ns
def mbuild(screen_name, message):
    return '@' + screen_name + ' ' + message + ' ' + rstring

error_message = ['You can\'t do that.', 'That can\'t be done.', 'Didn\'t work.', 'Oops, can\'t do that.', 'Sorry, you can\'t do that.', 'That didn\'t work.', 'Try something else.', 'Sorry, you\'ll have to try something else.', 'Oops, didn\'t work.', 'Oops, try something else.', 'Nice try, but you can\'t do that.', 'Nice try, but that didn\'t work.', 'Try something else, that didn\'t seem to work.']
# rstring to avoid Twitter getting mad about duplicate tweets // should think up a better solution for this
rstring = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
exclude = set(string.punctuation) # use to parse out from tweets

if __name__ == "__main__":
    twitter = TwitterAPI()

    # init mentions
    mentions = []

    # go through mentions from Twitter using Tweepy, gets the latest tweet from all players
    if debug == False:
        for mention in tweepy.Cursor(twitter.api.mentions_timeline).items():
            try:
                mentioned = False
                for m in mentions:
                    mention_name = (mention.text).split(' ',1)[0].lower()
                    if (mention.user.id == m['user_id']) or (mention_name != '@familiarlilt'): # if mention is already in mentioned, or the first word in mention text isn't lilt
                        mentioned = True
                if mentioned == False: # if user hasn't been mentioned, append it to mentions
                    mentions.append({
                        'screen_name': mention.user.screen_name,
                        'user_id': mention.user.id,
                        'text': mention.text,
                        'tweet_id': mention.id
                    })
            except:
                pass

    # mentions for testing purposes
    if debug == True:
        print 'Debugging...'
        debug_mentions = []
        d = 1
        while dbselect('screen_name', 'debug', 'tweet_id', str(d)) != None:
            debug_mentions.append({
                'screen_name': dbselect('screen_name', 'debug', 'tweet_id', str(d)),
                'user_id': int(dbselect('user_id', 'debug', 'tweet_id', str(d))),
                'text': dbselect('tweet', 'debug', 'tweet_id', str(d)), # update this with tweet to test
                'tweet_id': ''.join(random.choice(string.digits) for _ in range(18))
            })
            d += 1
        # go through mentions from Twitter using Tweepy, gets the latest tweet from all players
        for mention in debug_mentions:
            try:
                mentioned = False
                for m in mentions:
                    mention_name = (mention['text']).split(' ',1)[0].lower()
                    if (mention['user_id'] == m['user_id']) or (mention_name != '@familiarlilt'): # if user matches user already in mentions and if sent directly to Lilt
                        mentioned = True
                if mentioned == False: # if user hasn't been mentioned, append it to mentions
                    mentions.append({
                        'screen_name': mention['screen_name'],
                        'user_id': mention['user_id'],
                        'text': mention['text'],
                        'tweet_id': mention['tweet_id']
                    })
            except:
                pass
        print ' '

    # go through all mentions to see which require a response from Lilt
    for mention in mentions:
        try:
            screen_name = mention['screen_name'].lower()
            user_id = str(mention['user_id'])
            text = mention['text']
            tweet_id = str(mention['tweet_id'])
            reply = True if debug == True else False

            # splits tweet at first space, game_name = @familiarlilt (this should probably happen in the next loop)
            tweet = '' if len((text).split()) == 1 else (text).split(' ',1)[1]
            move = cleanstr(tweet)

            # attempts to grab current user from users table
            user_exists = dbselect('name', 'users', 'id', user_id)
            if user_exists == None:
                if move == 'start':
                    print 'new player: ' + screen_name
                    position = 'start'
                    inventory_init = {}
                    events_init = {}
                    events_init[position] = {}
                    cur.execute("INSERT INTO users (name, id, last_tweet_id, position, inventory, events) VALUES (%s, %s, %s, %s, %s, %s)", (screen_name, user_id, tweet_id, position, json.dumps(inventory_init), json.dumps(events_init)))
                    conn.commit()
                    reply = True
                else:
                    # this reply is purely for debugging - since reply defaults to True, this would be redundant
                    print screen_name + ' isn\'t playing Lilt.'
                    reply = False
            else:
                print "current player: " + screen_name
                tweet_exists = dbselect('name', 'users', 'last_tweet_id', tweet_id)
                if tweet_exists == None:
                    print "new tweet"
                    dbupdate(tweet_id, user_id, 'last_tweet_id')
                    reply = True
                else:
                    print "old tweet"

            # might want to add double check to make sure tweet sent
            # if this mention should be replied to, do so
            if reply == True:
                print 'tweet: ' + tweet
                # splits apart tweet to search for commands (drop/give)
                if len((tweet).split()) >= 2:
                    a, b = (tweet).split(' ',1)
                    a = ''.join(ch for ch in a if ch not in exclude).lower()
                    # if first word is drop - a is the move, b is the item
                    if (a == 'drop'):
                        # checks if item exists before changing move/item_to_drop based on it
                        if dbselect('name', 'items', 'name', cleanstr(b)) != None:
                            move = a
                            item_to_drop = cleanstr(b)
                    # if first word is give - break apart b
                    elif (a == 'give'):
                        # d will be the item, and c should be the recipient
                        c, d = (b).split(' ',1)
                        # checks if item exists before changing move/item_to_give based on it
                        if dbselect('name', 'items', 'name', cleanstr(d)) != None:
                            move = a
                            recipient = ''.join(ch for ch in c if ch not in exclude).lower()
                            item_to_give = cleanstr(d)
                print 'move: ' + move
                # get position
                position = dbselect('position', 'users', 'id', user_id)
                print 'position: ' + str(position)
                # get inventory
                inventory = json.loads(dbselect('inventory', 'users', 'id', user_id))
                print 'inventory: ' + str(inventory)
                # get events
                events = json.loads(dbselect('events', 'users', 'id', user_id))
                # add items to events_and_items
                events_and_items = events
                items = list(inventory.keys())
                for item in items:
                    events_and_items[position][item] = 'inventory'
                print 'events_and_items: ' + str(events_and_items)
                # get current event
                current_event = None
                for key, value in events_and_items[position].iteritems():
                    event = {}
                    event[key] = value
                    # check if there is a response for this move when condition is met (this event)
                    response = dbselect('response', 'moves', 'move', move, position, event)
                    if response != None:
                        current_event = event
                        break
                if current_event != None:
                    print 'current event: ' + str(current_event)
                # get response
                response = dbselect('response', 'moves', 'move', move, position, current_event)
                if response != None:
                    print 'response: ' + str(response)
                # get item (if one exists)
                item = dbselect('item', 'moves', 'move', move, position, current_event)
                if item != None:
                    print 'item: ' + str(item)
                # get drop (if one exists)
                drop = dbselect('drop', 'moves', 'move', move, position, current_event)
                if drop != None:
                    print 'drop: ' + str(drop)
                # get trigger for move and add it to events
                trigger = dbselect('trigger', 'moves', 'move', move, position, current_event)
                if trigger != None:
                    print 'trigger: ' + str(trigger)
                    trigger = json.loads(trigger)
                    events[position].update(trigger)
                    dbupdate(events, user_id, 'events')
                # get travel
                travel = dbselect('travel', 'moves', 'move', move, position, current_event)
                if travel != None:
                    print 'travel: ' + str(travel)
                    dbupdate(travel, user_id, 'position')
                    if travel not in events:
                        events[travel] = {}
                        dbupdate(events, user_id, 'events')

                # logic that generates response to player's move
                if move == 'drop':
                    message = mbuild(screen_name, dropitem(item_to_drop, inventory, user_id))
                elif move == 'give':
                    message = mbuild(screen_name, giveitem(item_to_give, inventory, user_id, position, recipient))
                elif (move == 'inventory') or (move == 'check inventory'):
                    if inventory == {}:
                        message = mbuild(screen_name, 'Your inventory is empty at the moment.')
                    else:
                        message = mbuild(screen_name, invbuild(inventory))
                else:
                    print 'Searching...'
                    if response != None:
                        if (item != None) and (drop != None):
                            print 'We\'re going to be dealing with an item and drop.'
                            message = mbuild(screen_name, replaceitem(item, drop, inventory, user_id, response))
                        elif item != None:
                            print 'Alright, I\'m going to get that item for you... if you can hold it.'
                            message = mbuild(screen_name, getitem(item, inventory, user_id, response))
                        elif drop != None:
                            print 'So you\'re just dropping/burning an item.'
                            message = mbuild(screen_name, dropitem(drop, inventory, user_id, response))
                        else:
                            print 'Got one!'
                            message = mbuild(screen_name, response)
                    else:
                        print "I guess that move didn't work."
                        message = mbuild(screen_name, random.choice(error_message))
                        print storeerror(move, position)

                print "reply: " + message
                if debug == False:
                    print "#TweetingIt"
                    twitter.reply(message, tweet_id)
            print " "
        except:
            pass
cur.close()
conn.close()
