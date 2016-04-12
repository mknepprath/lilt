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

def item():
    print "Item management function will go here."

def getitem(item, inventory, user_id, response):
    # update values here: items, triggers, etc
    if item not in inventory:
        inventory[item] = {}
        inventory[item]['quantity'] = 1
        # check if there's room in the inventory
        if len(mbuild('x'*15, invbuild(inventory))) >= 140:
            return 'Your inventory is full.'
        else:
            # update database with updated values
            dbupdate(inventory, user_id)
            return response
    else:
        print 'You already have 1 or more of that item.'
        item_max = dbselect('max', 'items', 'name', item)
        print 'Got the quantity you\'re able to carry of that item.'
        if inventory[item]['quantity'] < item_max:
            print 'You have less than the limit.'
            inventory[item]['quantity'] += 1
            # check if there's room in the inventory
            if len(mbuild('x'*15, invbuild(inventory))) >= 140:
                print 'You\'re inventory is full, though.'
                return 'Your inventory is full.'
            else:
                print 'You have room for it in your inventory, so I\'ll add it.'
                dbupdate(inventory, user_id)
                return response
        else:
            print 'You\'ve reached the limit for that item.'
            return 'You can\'t hold more ' + item + '!'

def dropitem(item, inventory, user_id):
    if item not in inventory:
        return 'You don\'t have anything like that.'
    elif inventory[item]['quantity'] <= 1:
        del inventory[item]
        dbupdate(inventory, user_id)
        return 'You drop one ' + item + '.'
    else:
        inventory[item]['quantity'] -= 1
        dbupdate(inventory, user_id)
        return 'You drop one ' + item + '.'

def giveitem(item, inventory, user_id, position, recipient):
    print 'So you want to give ' + item + ' to ' + recipient + '.'
    if item not in inventory:
        print item + ' wasn\'t in your inventory.' #TESTING
        return 'You don\'t have ' + item + '!'
    else:
        print 'Okay, so you do have the item.' #TESTING
        #check if item can be given
        givable = dbselect('give', 'items', 'name', item)
        print 'Givableness of item should be above this...'
        if givable == False:
            print 'Can\'t give that away!'
            return item.capitalize() + ' can\'t be given.'
        else:
            #check if recipient exists
            recipient_id = dbselect('id', 'users', 'name', recipient)
            if recipient_id == None:
                print 'Yeah, that person doesn\'t exist.' #TESTING
                return 'They aren\'t playing Lilt!'
            else:
                # get recipient inventory
                recipient_position = dbselect('position', 'users', 'id', recipient_id)
                print 'Got the position for recipient, I think.' #TESTING
                # might be better to have a default value in users, but this checks to see if empty and creates dict if it is
                if recipient_position != position:
                    print 'You aren\'t close enough to the recipient to give them anything.' #TESTING
                    return 'You aren\'t close enough to them to give them that!'
                else:
                    # get recipient inventory
                    recipient_inventory = json.loads(dbselect('inventory', 'users', 'id', recipient_id))
                    print 'Got the recipient\'s inventory.' #TESTING
                    # modify recipient inventory, see if it fits
                    if item not in recipient_inventory:
                        print 'Oh yeah, they didn\'t have that item.'
                        recipient_inventory[item] = {}
                        recipient_inventory[item]['quantity'] = 1
                        if inventory[item]['quantity'] <= 1:
                            del inventory[item]
                        else:
                            inventory[item]['quantity'] -= 1
                        # check if there's room in the inventory
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
                            # check if there's room in the inventory
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
            print item
            print str(inventory)
            print str(inventory[item])
            print inventory[item]['quantity']
            print item_max
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

def mbuild(screen_name, message):
    return '@' + screen_name + ' ' + message + ' ' + rstring

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
    if (col != 'inventory') and (col != 'events'):
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (val1, val2))
    elif col == 'attempts':
        cur.execute("UPDATE attempts SET " + col + " = %s WHERE move = %s", (val1, val2))
    else:
        cur.execute("UPDATE users SET " + col + " = %s WHERE id = %s;", (json.dumps(val1), val2))
    conn.commit()

error_message = ["You can't do that.", "That can't be done.", "Didn't work.", "Oops, can't do that.", "Sorry, you can't do that.", "That didn't work.", "Try something else.", "Sorry, you'll have to try something else.", "Oops, didn't work.", "Oops, try something else.", "Nice try, but you can't do that.", "Nice try, but that didn't work.", "Try something else, that didn't seem to work."]

# rstring to avoid Twitter getting mad about duplicate tweets // should think up a better solution for this
rstring = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
print 'String of random characters created.'

if __name__ == "__main__":
    twitter = TwitterAPI()

    # init mentions
    mentions = []

    # mentions for testing purposes
    if debug == True:
        debug_tweet = dbselect('tweet', 'debug', 'tweet_id', '1')
        mentions.append({
            'screen_name': 'mknepprath',
            'user_id': 15332057,
            'tweet': debug_tweet, # update this with tweet to test
            'tweet_id': ''.join(random.choice(string.digits) for _ in range(18))
        })

    # go through mentions from Twitter using Tweepy
    if debug == False:
        for mention in tweepy.Cursor(twitter.api.mentions_timeline).items():
            try:
                # splits tweet at first space, game_name = @familiarlilt (this should probably happen in the next loop)
                if len((mention.text).split()) == 1:
                    # clarifying this for myself... if the tweet is only 1 word, it's just the name '@familiarlilt', so no command
                    tweet = ''
                else:
                    game_name, tweet = (mention.text).split(' ',1)

                # init mentioned
                mentioned = False
                # runs through mentions and notes if current user has been mentioned
                for m in mentions:
                    try:
                        if mention.user.id == m['user_id']:
                            mentioned = True
                    except:
                        pass

                # if user hasn't been mentioned, append it to mentions
                if mentioned == False:
                    mentions.append({
                        'screen_name': mention.user.screen_name,
                        'user_id': mention.user.id,
                        'tweet': tweet,
                        'tweet_id': mention.id
                    })

            except:
                pass

    # go through all mentions that require a response from Lilt
    for mention in mentions:
        try:
            screen_name = mention['screen_name']
            user_id = str(mention['user_id'])
            tweet = mention['tweet']
            tweet_id = str(mention['tweet_id'])
            reply = False

            # when debugging, always reply (even if tweet id is the same)
            if debug == True:
                reply = True

            # clean up tweet and break it apart
            # removes punctuation, links, extra whitespace, and makes move lowercase
            tweet_mod = re.sub(r'http\S+', '', tweet)
            tweet_mod = re.sub(' +',' ', tweet_mod)
            exclude = set(string.punctuation) # using this later, as well - maybe init at beginning?
            move = ''.join(ch for ch in tweet_mod if ch not in exclude).lower().rstrip()

            # attempts to grab current user from users table
            user_exists = dbselect('name', 'users', 'id', user_id)
            # if they're in the table, grab tweet id from table
            if user_exists != None:
                print "current player: " + screen_name
                tweet_exists = dbselect('name', 'users', 'last_tweet_id', tweet_id)
                # if tweet_id isn't in users table, update tweet_id
                if tweet_exists == None:
                    print "new tweet"
                    dbupdate(tweet_id, user_id, 'last_tweet_id')
                    reply = True
                # otherwise, do nothing - tweet has already been replied to
                else:
                    print "old tweet"
            else:
                if move == 'start':
                    # if user is not in the users table, add user and tweet_id
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
                    reply = False
                    print 'This person isn\'t playing Lilt.'

            # might want to add double check to make sure tweet sent
            # if this mention should be replied to, do so
            if reply == True:

                # if tweet is two words or more, break off first word
                if len((tweet).split()) >= 2:
                    a, b = (tweet).split(' ',1)
                    a = ''.join(ch for ch in a if ch not in exclude).lower()
                    # if first word is drop - a is the move, b is the item
                    if (a == 'drop'):
                        move = a
                        item_to_drop = ''.join(ch for ch in b if ch not in exclude).lower()
                    # if first word is give - break apart b
                    elif (a == 'give'):
                        move = a
                        # c will be the item, and b should be the recipient
                        c, d = (b).split(' ',1)
                        recipient = ''.join(ch for ch in c if ch not in exclude).lower()
                        item_to_give = ''.join(ch for ch in d if ch not in exclude).lower()
                print "move: " + move

                # get position
                position = dbselect('position', 'users', 'id', user_id)
                print "position: " + str(position)

                # get inventory
                inventory = json.loads(dbselect('inventory', 'users', 'id', user_id))
                print "inventory: " + str(inventory)

                # get events
                events = json.loads(dbselect('events', 'users', 'id', user_id))
                print "events: " + str(events)

                # add items to events_and_items
                events_and_items = events
                items = list(inventory.keys())
                for item in items:
                    events_and_items[position][item] = 'inventory'
                print "events_and_items: " + str(events_and_items)

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
                print "current event: " + str(current_event)

                # get response
                response = dbselect('response', 'moves', 'move', move, position, current_event)
                print "response: " + str(response)

                # get item (if one exists)
                item = dbselect('item', 'moves', 'move', move, position, current_event)
                print "item: " + str(item)

                # get drop (if one exists)
                drop = dbselect('drop', 'moves', 'move', move, position, current_event)
                print "drop: " + str(drop)

                # get trigger for move and add it to events
                trigger = dbselect('trigger', 'moves', 'move', move, position, current_event)
                # if there is a trigger, add it
                if trigger != None:
                    trigger = json.loads(trigger)
                    print "trigger: " + str(trigger)
                    if position not in events:
                        # add position dict item to events if it's not there yet
                        events[position] = {}
                        print "Position wasn't in events, so I added it."
                    # add trigger to events (this adds or updates current value at key of trigger)
                    events[position].update(trigger)
                    print "Trigger added under the current location in events."
                    dbupdate(events, user_id, 'events')
                    print "Updated db with updated events."

                # get travel
                travel = dbselect('travel', 'moves', 'move', move, position, current_event)
                print "travel: " + str(travel)
                if travel != None:
                    print "Records indicate that you will be traveling,"
                    dbupdate(travel, user_id, 'position')
                    if travel not in events:
                        events[travel] = {}
                        dbupdate(events, user_id, 'events')
                    print "so I've updated your position."

                # logic that generates response to player's move
                if move == 'drop':
                    message = mbuild(screen_name, dropitem(item_to_drop, inventory, user_id))
                elif move == 'give':
                    message = mbuild(screen_name, giveitem(item_to_give, inventory, user_id, position, recipient))
                elif move == 'inventory':
                    if inventory == {}:
                        print 'Empty inventory check worked, I guess.'
                        message = mbuild(screen_name, 'Your inventory is empty at the moment.')
                    else:
                        message = mbuild(screen_name, invbuild(inventory))
                else:
                    print 'Looks like we\'re going to dive into the db for responses.'
                    if response != None:
                        if item != None:
                            print 'We\'re going to be dealing with an item, as well.'
                            # if there is an item that the new item is replacing...
                            if drop != None:
                                print 'Also going to be dropping an item.'
                                message = mbuild(screen_name, replaceitem(item, drop, inventory, user_id, response))
                            else:
                                print 'Alright, I\'m going to get that item for you... if you can hold it.'
                                message = mbuild(screen_name, getitem(item, inventory, user_id, response))
                        # if there isn't an item...
                        else:
                            print 'Got one! Just a stock response.'
                            message = mbuild(screen_name, response)
                    else:
                        print "I guess that move didn't work."
                        message = mbuild(screen_name, random.choice(error_message))
                        print storeerror(move, position)

                print "reply: " + message
                if debug == False:
                    print "#TweetingIt"
                    twitter.reply(message, tweet_id)
        except:
            pass
cur.close()
conn.close()
