# -*- coding: utf-8 -*-
import os
import time
import string
import random
import tweepy
import psycopg2
import urlparse
import json
import item
import event
import command
import db
from utils import cleanstr, mbuild, invbuild

# debugging options
debug = False
rec = False # pushs logs to console table // unicode doesn't work when debugging...

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

error_message = ['You can\'t do that.', 'That can\'t be done.', 'Didn\'t work.', 'Oops, can\'t do that.', 'Sorry, you can\'t do that.', 'That didn\'t work.', 'Try something else.', 'Sorry, you\'ll have to try something else.', 'Oops, didn\'t work.', 'Oops, try something else.', 'Nice try, but you can\'t do that.', 'Nice try, but that didn\'t work.', 'Try something else, that didn\'t seem to work.']
# rstring = ''.join(random.choice(string.ascii_uppercase + string.digits + u'\u2669' + u'\u266A' + u'\u266B' + u'\u266C' + u'\u266D' + u'\u266E' + u'\u266F') for _ in range(5))

if __name__ == "__main__":
    twitter = TwitterAPI()

    # init mentions
    mentions = []

    # delete console table before entering new logs
    if rec == True:
        db.delete('console', 'log', '*')

    # get latest tweets
    if debug == False:
        raw_mentions = twitter.api.mentions_timeline(count=200)
        # get builder mentions
        builder = False
        for mention in raw_mentions: # do these get processed first...
            if mention.user.id == 724754312757272576:
                if mention.id == int(db.select('last_tweet_id', 'users', 'id', '724754312757272576')):
                    builder = True
            if builder == False:
                mentions.append({
                    'screen_name': mention.user.screen_name,
                    'user_id': mention.user.id,
                    'text': mention.text,
                    'tweet_id': mention.id
                })
            else:
                break
        # gets the rest of the mentions
        for mention in raw_mentions:
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

    # get debug tweets
    if debug == True:
        db.log(rec, 'Debugging...')
        debug_mentions = []
        d = 1
        while db.select('screen_name', 'debug', 'tweet_id', str(d)) != None:
            debug_mentions.append({
                'screen_name': db.select('screen_name', 'debug', 'tweet_id', str(d)),
                'user_id': int(db.select('user_id', 'debug', 'tweet_id', str(d))),
                'text': db.select('tweet', 'debug', 'tweet_id', str(d)), # update this with tweet to test
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
        db.log(rec, ' ')

    # go through all mentions to see which require a response from Lilt
    for mention in mentions:
        try:
            user = {}
            user['screen_name'] = mention['screen_name'].lower()
            user['id'] = str(mention['user_id'])
            user['text'] = mention['text']
            user['tweet_id'] = str(mention['tweet_id'])

            reply = True if debug == True else False
            cmdreply = False
            cmd = ''

            # gets tweet user['text'] sans @familiarlilt - removes @lilt_bird (or other @xxxxx) if included in tweet
            tweet = '' if len((user['text']).split()) == 1 else (user['text']).split(' ',1)[1]
            if (tweet).split(' ',1)[0][0] == '@':
                tweet = (tweet).split(' ',1)[1]
            move = cleanstr(tweet)

            # attempts to grab current user from users table
            user_exists = db.select('name', 'users', 'id', user['id'])
            if user_exists == None:
                if move == 'start':
                    db.log(rec, 'new player: ' + user['screen_name'])
                    position_init = 'start'
                    inventory_init = {}
                    events_init = {}
                    events_init[position_init] = {}
                    db.newuser(user['screen_name'], user['id'], user['tweet_id'], position_init, inventory_init, events_init)
                    reply = True
                else:
                    # this reply is purely for debugging - since reply defaults to True, this would be redundant
                    db.log(rec, user['screen_name'] + ' isn\'t playing Lilt.')
                    reply = False
            else:
                db.log(rec, 'current player: ' + user['screen_name'])
                tweet_exists = db.select('name', 'users', 'last_tweet_id', user['tweet_id'])
                if tweet_exists == None:
                    db.log(rec, 'new tweet')
                    db.update(user['tweet_id'], user['id'], 'last_tweet_id')
                    reply = True
                else:
                    db.log(rec, 'old tweet')

            # if this mention should be replied to, do so # might want to add double check to make sure tweet sent
            if reply == True:
                db.log(rec, 'tweet: ' + tweet)
                # loop through requests to users table
                user_data = ['position', 'inventory', 'events']
                for r in user_data:
                    user[r] = db.select(r, 'users', 'id', user['id']) if r == 'position' else json.loads(db.select(r, 'users', 'id', user['id'])) # can json.loads get moved into db.select function?
                    db.log(rec, r + ': ' + str(user[r]))
                # handles commands (drop/give/inventory)
                cmdreply, cmd = command.get(tweet, user['inventory'], user['id'], user['position'])
                if not cmdreply:
                    # get data for db response
                    db.log(rec, 'move: ' + move)
                    # get current event (requires items from user_data)
                    user['current_event'] = event.getcurrent(move, user['position'], user['inventory'], user['events'])
                    if user['current_event'] != None:
                        db.log(rec, 'current event: ' + str(user['current_event']))
                    # loop through requests to moves table (requires current_event)
                    move_data = ['response', 'item', 'drop', 'trigger', 'travel']
                    for r in move_data:
                        user[r] = db.select(r, 'moves', 'move', move, user['position'], user['current_event'])
                        if user[r] != None:
                            db.log(rec, r + ': ' + str(user[r]))
                    # add trigger to events if it exists for this move
                    if user['trigger'] != None:
                        user['trigger'] = json.loads(user['trigger'])
                        user['events'][user['position']].update(user['trigger'])
                        db.update(user['events'], user['id'], 'events')
                    # move user if travel exists and add new position to events
                    if user['travel'] != None:
                        db.update(user['travel'], user['id'], 'position')
                        if user['travel'] not in user['events']:
                            user['events'][user['travel']] = {}
                            db.update(user['events'], user['id'], 'events')
                    # get a response
                    db.log(rec, 'Searching...')
                    if user['response'] != None:
                        if (user['item'] != None) and (user['drop'] != None):
                            message = mbuild(user['screen_name'], item.replace(user['item'], user['drop'], user['inventory'], user['id'], user['response']))
                        elif user['item'] != None:
                            message = mbuild(user['screen_name'], item.get(user['item'], user['inventory'], user['id'], user['response']))
                        elif user['drop'] != None:
                            message = mbuild(user['screen_name'], item.drop(user['drop'], user['inventory'], user['id'], user['response']))
                        else:
                            message = mbuild(user['screen_name'], user['response'])
                    else:
                        db.log(rec, 'I guess that move didn\'t work.')
                        message = mbuild(user['screen_name'], random.choice(error_message))
                        if debug == False:
                            db.log(rec, db.storeerror(move, user['position']))
                else:
                    db.log(rec, 'command response: ' + str(cmd))
                    message = mbuild(user['screen_name'], cmd)

                db.log(rec, 'reply: ' + message)
                if debug == False:
                    db.log(rec, '#TweetingIt')
                    twitter.reply(message, user['tweet_id'])
            db.log(rec, ' ') # prints user data separate from other logs
            db.log(rec, user['screen_name'] + '\'s data: ' + str(user))
            db.log(rec, ' ')
        except:
            pass
db.cur.close()
db.conn.close()
