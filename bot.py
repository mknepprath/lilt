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
import item
from utils import cleanstr, mbuild, invbuild
from db import log

# debugging options
debug = True
rec = True # pushs logs to console table // breaks emoji when True

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

error_message = ['You can\'t do that.', 'That can\'t be done.', 'Didn\'t work.', 'Oops, can\'t do that.', 'Sorry, you can\'t do that.', 'That didn\'t work.', 'Try something else.', 'Sorry, you\'ll have to try something else.', 'Oops, didn\'t work.', 'Oops, try something else.', 'Nice try, but you can\'t do that.', 'Nice try, but that didn\'t work.', 'Try something else, that didn\'t seem to work.']
# rstring to avoid Twitter getting mad about duplicate tweets - unnecessary at the moment ### rstring = ''.join(random.choice(string.ascii_uppercase + string.digits + u'\u2669' + u'\u266A' + u'\u266B' + u'\u266C' + u'\u266D' + u'\u266E' + u'\u266F') for _ in range(5))

if __name__ == "__main__":
    twitter = TwitterAPI()

    # init mentions
    mentions = []

    # delete console table before entering new logs
    if rec == True:
        cur.execute("DELETE FROM console WHERE log != '*';")
        conn.commit()

    # get latest tweets
    if debug == False:
        try:
            raw_mentions = twitter.api.mentions_timeline(count=200)
        except twitter.TweepError, e:
            log(rec, 'Failed because of %s' % e.reason)
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

    # get debug tweets
    if debug == True:
        log(rec, 'Debugging...')
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
        log(rec, ' ')

    # go through all mentions to see which require a response from Lilt
    for mention in mentions:
        try:
            user = {}
            user['screen_name'] = mention['screen_name'].lower()
            user['id'] = str(mention['user_id'])
            user['text'] = mention['text']
            user['tweet_id'] = str(mention['tweet_id'])

            reply = True if debug == True else False

            # gets tweet user['text'] sans @familiarlilt - removes @lilt_bird (or other @xxxxx) if included in tweet
            tweet = '' if len((user['text']).split()) == 1 else (user['text']).split(' ',1)[1]
            if (tweet).split(' ',1)[0][0] == '@':
                tweet = (tweet).split(' ',1)[1]
            move = cleanstr(tweet)

            # attempts to grab current user from users table
            user_exists = dbselect('name', 'users', 'id', user['id'])
            if user_exists == None:
                if move == 'start':
                    log(rec, 'new player: ' + user['screen_name'])
                    position_init = 'start'
                    inventory_init = {}
                    events_init = {}
                    events_init[position_init] = {}
                    cur.execute("INSERT INTO users (name, id, last_tweet_id, position, inventory, events) VALUES (%s, %s, %s, %s, %s, %s)", (user['screen_name'], user['id'], user['tweet_id'], position_init, json.dumps(inventory_init), json.dumps(events_init)))
                    conn.commit()
                    reply = True
                else:
                    # this reply is purely for debugging - since reply defaults to True, this would be redundant
                    log(rec, user['screen_name'] + ' isn\'t playing Lilt.')
                    reply = False
            else:
                log(rec, 'current player: ' + user['screen_name'])
                tweet_exists = dbselect('name', 'users', 'last_tweet_id', user['tweet_id'])
                if tweet_exists == None:
                    log(rec, 'new tweet')
                    dbupdate(user['tweet_id'], user['id'], 'last_tweet_id')
                    reply = True
                else:
                    log(rec, 'old tweet')

            # if this mention should be replied to, do so # might want to add double check to make sure tweet sent
            if reply == True:
                log(rec, 'tweet: ' + tweet)
                # splits apart tweet to search for commands (drop/give)
                if len((tweet).split()) >= 2:
                    a, b = (tweet).split(' ',1)
                    a = ''.join(ch for ch in a if ch not in set(string.punctuation)).lower()
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
                            recipient = ''.join(ch for ch in c if ch not in set(string.punctuation)).lower()
                            item_to_give = cleanstr(d)
                    elif (a == 'liltadd') and ((user['id'] == '15332057') or (user['id'] == '724754312757272576')):
                        # @familiarlilt liltadd look at sign~Wow, that's a big sign.
                        e, f = (b).split('~',1)
                        move = a
                        addmove = str(e)
                        addresponse = str(f)
                log(rec, 'move: ' + move)
                # loop through requests to users table
                user_requests = ['position', 'inventory', 'events']
                for r in user_requests:
                    user[r] = dbselect(r, 'users', 'id', user['id']) if r == 'position' else json.loads(dbselect(r, 'users', 'id', user['id'])) # can json.loads get moved into dbselect function?
                    log(rec, r + ': ' + str(user[r]))
                # get current event (requires prev three items)
                user['current_event'] = getcurrentevent(move, user['position'], user['inventory'], user['events'])
                if user['current_event'] != None:
                    log(rec, 'current event: ' + str(user['current_event']))
                # loop through requests to moves table (requires current_event)
                move_requests = ['response', 'item', 'drop', 'trigger', 'travel']
                for r in move_requests:
                    user[r] = dbselect(r, 'moves', 'move', move, user['position'], user['current_event'])
                    if user[r] != None:
                        log(rec, r + ': ' + str(user[r]))
                # add trigger to events if it exists for this move
                if user['trigger'] != None:
                    user['trigger'] = json.loads(user['trigger'])
                    user['events'][user['position']].update(user['trigger'])
                    dbupdate(user['events'], user['id'], 'events')
                # move user if travel exists and add new position to events
                if user['travel'] != None:
                    dbupdate(user['travel'], user['id'], 'position')
                    if user['travel'] not in user['events']:
                        user['events'][user['travel']] = {}
                        dbupdate(user['events'], user['id'], 'events')

                # logic that generates response to player's move
                if move == 'drop':
                    message = mbuild(user['screen_name'], item.drop(item_to_drop, user['inventory'], user['id']))
                elif move == 'give':
                    message = mbuild(user['screen_name'], item.give(item_to_give, user['inventory'], user['id'], user['position'], recipient))
                elif move == 'liltadd':
                    cur.execute("INSERT INTO moves (move, response, position) VALUES (%s, %s, %s)", (addmove,addresponse,user['position']))
                    conn.commit()
                    message = mbuild(user['screen_name'], '\'' + addmove + '\' was added to Lilt.')
                elif (move == 'inventory') or (move == 'check inventory'):
                    if user['inventory'] == {}:
                        message = mbuild(user['screen_name'], 'Your inventory is empty at the moment.')
                    else:
                        message = mbuild(user['screen_name'], invbuild(user['inventory']))
                elif (move == 'delete me from lilt') or (move == u'💀💀💀'):
                    message = mbuild(user['screen_name'], 'You\'ve been removed from Lilt. Thanks for playing!')
                    cur.execute("DELETE FROM users WHERE id = %s;", (user['id'],))
                    conn.commit()
                else:
                    log(rec, 'Searching...')
                    if user['response'] != None:
                        if (user['item'] != None) and (user['drop'] != None):
                            log(rec, 'We\'re going to be dealing with an item and drop.')
                            message = mbuild(user['screen_name'], item.replace(user['item'], user['drop'], user['inventory'], user['id'], user['response']))
                        elif user['item'] != None:
                            log(rec, 'Alright, I\'m going to get that item for you... if you can hold it.')
                            message = mbuild(user['screen_name'], item.get(user['item'], user['inventory'], user['id'], user['response']))
                        elif user['drop'] != None:
                            log(rec, 'So you\'re just dropping/burning an item.')
                            message = mbuild(user['screen_name'], item.drop(user['drop'], user['inventory'], user['id'], user['response']))
                        else:
                            log(rec, 'Got one!')
                            message = mbuild(user['screen_name'], user['response'])
                    else:
                        log(rec, 'I guess that move didn\'t work.')
                        message = mbuild(user['screen_name'], random.choice(error_message))
                        log(rec, storeerror(move, user['position']))

                log(rec, 'reply: ' + message)
                if debug == False:
                    log(rec, '#TweetingIt')
                    try:
                        twitter.reply(message, user['tweet_id'])
                    except twitter.TweepError, e:
                        log(rec, 'Failed because of %s' % e.reason)
            log(rec, ' ') # prints user data separate from other logs
            log(rec, user['screen_name'] + '\'s data: ' + str(user))
            log(rec, ' ')
        except:
            pass
cur.close()
conn.close()
