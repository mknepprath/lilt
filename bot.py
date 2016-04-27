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
logbugs = True # breaks emoji when True

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
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

    def tweet(self, message):
        """Send a tweet"""
        self.api.update_status(status=message)

    def reply(self, message, tweet_id):
        """Reply to a tweet"""
        self.api.update_status(status=message, in_reply_to_status_id=tweet_id)

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
    ns = ''.join(ch for ch in s_mod if ch not in exclude).lower().rstrip() # removes punctuation
    return ns
def storeerror(move, position):
    attempt = dbselect('attempts', 'attempts', 'move', move, position)
    if attempt == None:
        cur.execute("INSERT INTO attempts (move, position, attempts) VALUES (%s, %s, %s)", (str(move),str(position),1))
        conn.commit()
    else:
        dbupdate(attempt+1, move, 'attempts')
    return "Stored the failed attempt for future reference."
def log(s):
    if logbugs == True:
        cur.execute("INSERT INTO console (log, time) VALUES (%s, 'now')", (str(s),))
        conn.commit()
        print str(s)
        return
    else:
        pass

error_message = ['You can\'t do that.', 'That can\'t be done.', 'Didn\'t work.', 'Oops, can\'t do that.', 'Sorry, you can\'t do that.', 'That didn\'t work.', 'Try something else.', 'Sorry, you\'ll have to try something else.', 'Oops, didn\'t work.', 'Oops, try something else.', 'Nice try, but you can\'t do that.', 'Nice try, but that didn\'t work.', 'Try something else, that didn\'t seem to work.']
# rstring to avoid Twitter getting mad about duplicate tweets // should think up a better solution for this
rstring = ''.join(random.choice(string.ascii_uppercase + string.digits + u'\u2669' + u'\u266A' + u'\u266B' + u'\u266C' + u'\u266D' + u'\u266E' + u'\u266F') for _ in range(5))
exclude = set(string.punctuation) # use to parse out from tweets

if __name__ == "__main__":
    twitter = TwitterAPI()

    # init mentions
    mentions = []

    # delete console table
    # cur.execute("DELETE FROM console WHERE log != '*';")
    # conn.commit()

    # go through mentions from Twitter using Tweepy, gets the latest tweet from all players
    if debug == False:
        try:
            raw_mentions = twitter.api.mentions_timeline(count=200)
        except twitter.TweepError, e:
            log('Failed because of %s' % e.reason)
        for mention in raw_mentions:
            try:
                mentioned = False
                mention_name = (mention.text).split(' ',1)[0].lower()
                if mention_name != '@familiarlilt':
                    mentioned = True
                for m in mentions:
                    if mention.user.id == m['user_id']: # if mention is already in mentioned, or the first word in mention text isn't lilt
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
        log('Debugging...')
        debug_mentions = []
        d = 1
        while dbselect('screen_name', 'debug', 'tweet_id', str(d)) != None:
            debug_mentions.append({
                'screen_name': dbselect('screen_name', 'debug', 'tweet_id', str(d)),
                'user_id': int(dbselect('user_id', 'debug', 'tweet_id', str(d))),
                'text': unicode(dbselect('tweet', 'debug', 'tweet_id', str(d))), # update this with tweet to test
                'tweet_id': ''.join(random.choice(string.digits) for _ in range(18))
            })
            d += 1
        print '1'
        # go through mentions from Twitter using Tweepy, gets the latest tweet from all players
        for mention in debug_mentions:
            try:
                mentioned = False
                mention_name = (mention['text']).split(' ',1)[0].lower()
                if mention_name != '@familiarlilt':
                    mentioned = True
                for m in mentions:
                    if mention['user_id'] == m['user_id']: # if user matches user already in mentions and if sent directly to Lilt
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
            print '2'
        log(' ')
        print '3'

    # go through all mentions to see which require a response from Lilt
    for mention in mentions:
        try:
            print '4'
            user = {}
            user['screen_name'] = mention['screen_name'].lower()
            user['id'] = str(mention['user_id'])
            user['text'] = mention['text']
            user['tweet_id'] = str(mention['tweet_id'])
            print '5'

            reply = True if debug == True else False
            print '6'
            print str(user)

            # gets tweet user.text sans @familiarlilt - removes @lilt_bird (or other @xxxxx) if included in tweet
            tweet = '' if len((user.text).split()) == 1 else (user.text).split(' ',1)[1]
            if (tweet).split(' ',1)[0][0] == '@':
                tweet = (tweet).split(' ',1)[1]
            move = cleanstr(tweet)
            print '7'

            # attempts to grab current user from users table
            user_exists = dbselect('name', 'users', 'id', user.id)
            if user_exists == None:
                if move == 'start':
                    log('new player: ' + user.screen_name)
                    position = 'start'
                    inventory_init = {}
                    events_init = {}
                    events_init[position] = {}
                    cur.execute("INSERT INTO users (name, id, last_tweet_id, position, inventory, events) VALUES (%s, %s, %s, %s, %s, %s)", (user.screen_name, user.id, user.tweet_id, position, json.dumps(inventory_init), json.dumps(events_init)))
                    conn.commit()
                    reply = True
                else:
                    # this reply is purely for debugging - since reply defaults to True, this would be redundant
                    log(user.screen_name + ' isn\'t playing Lilt.')
                    reply = False
            else:
                log('current player: ' + user.screen_name)
                tweet_exists = dbselect('name', 'users', 'last_tweet_id', user.tweet_id)
                if tweet_exists == None:
                    log('new tweet')
                    dbupdate(user.tweet_id, user.id, 'last_tweet_id')
                    reply = True
                else:
                    log('old tweet')
            print '8'

            # if this mention should be replied to, do so # might want to add double check to make sure tweet sent
            if reply == True:
                log('tweet: ' + tweet)
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
                    elif (a == 'liltadd') and ((user.id == '15332057') or (user.id == '724754312757272576')):
                        # @familiarlilt liltadd look at sign~Wow, that's a big sign.
                        e, f = (b).split('~',1)
                        move = a
                        addmove = str(e)
                        addresponse = str(f)
                log('move: ' + move)
                # get position
                position = dbselect('position', 'users', 'id', user.id)
                log('position: ' + str(position))
                # get inventory
                inventory = json.loads(dbselect('inventory', 'users', 'id', user.id))
                log('inventory: ' + str(inventory))
                # get events
                events = json.loads(dbselect('events', 'users', 'id', user.id))
                # add items to events_and_items
                events_and_items = events
                items = list(inventory.keys())
                for item in items:
                    events_and_items[position][item] = 'inventory'
                log('events_and_items: ' + str(events_and_items))
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
                    log('current event: ' + str(current_event))
                # get response
                response = dbselect('response', 'moves', 'move', move, position, current_event)
                if response != None:
                    log('response: ' + str(response))
                # get item (if one exists)
                item = dbselect('item', 'moves', 'move', move, position, current_event)
                if item != None:
                    log('item: ' + str(item))
                # get drop (if one exists)
                drop = dbselect('drop', 'moves', 'move', move, position, current_event)
                if drop != None:
                    log('drop: ' + str(drop))
                # get trigger for move and add it to events
                trigger = dbselect('trigger', 'moves', 'move', move, position, current_event)
                if trigger != None:
                    log('trigger: ' + str(trigger))
                    trigger = json.loads(trigger)
                    events[position].update(trigger)
                    dbupdate(events, user.id, 'events')
                # get travel
                travel = dbselect('travel', 'moves', 'move', move, position, current_event)
                if travel != None:
                    log('travel: ' + str(travel))
                    dbupdate(travel, user.id, 'position')
                    if travel not in events:
                        events[travel] = {}
                        dbupdate(events, user.id, 'events')

                # logic that generates response to player's move
                if move == 'drop':
                    message = mbuild(user.screen_name, dropitem(item_to_drop, inventory, user.id))
                elif move == 'give':
                    message = mbuild(user.screen_name, giveitem(item_to_give, inventory, user.id, position, recipient))
                elif move == 'liltadd':
                    cur.execute("INSERT INTO moves (move, response, position) VALUES (%s, %s, %s)", (addmove,addresponse,position))
                    conn.commit()
                    message = mbuild(user.screen_name, '\'' + addmove + '\' was added to Lilt.')
                elif (move == 'inventory') or (move == 'check inventory'):
                    if inventory == {}:
                        message = mbuild(user.screen_name, 'Your inventory is empty at the moment.')
                    else:
                        message = mbuild(user.screen_name, invbuild(inventory))
                elif (move == 'delete me from lilt') or (move == u'💀💀💀'):
                    message = mbuild(user.screen_name, 'You\'ve been removed from Lilt. Thanks for playing!')
                    cur.execute("DELETE FROM users WHERE id = %s;", (user.id,))
                    conn.commit()
                else:
                    log('Searching...')
                    if response != None:
                        if (item != None) and (drop != None):
                            log('We\'re going to be dealing with an item and drop.')
                            message = mbuild(user.screen_name, replaceitem(item, drop, inventory, user.id, response))
                        elif item != None:
                            log('Alright, I\'m going to get that item for you... if you can hold it.')
                            message = mbuild(user.screen_name, getitem(item, inventory, user.id, response))
                        elif drop != None:
                            log('So you\'re just dropping/burning an item.')
                            message = mbuild(user.screen_name, dropitem(drop, inventory, user.id, response))
                        else:
                            log('Got one!')
                            message = mbuild(user.screen_name, response)
                    else:
                        log('I guess that move didn\'t work.')
                        message = mbuild(user.screen_name, random.choice(error_message))
                        log(storeerror(move, position))

                log('reply: ' + message)
                if debug == False:
                    log('#TweetingIt')
                    try:
                        twitter.reply(message, user.tweet_id)
                    except twitter.TweepError, e:
                        log('Failed because of %s' % e.reason)
            log(' ')
        except:
            pass
cur.close()
conn.close()
