"""Bot."""
# -*- coding: utf-8 -*-
import os
import string
import random
import json
import tweepy
import item
import event
import command
import db
from utils import cleanstr, mbuild

# debugging options
DEBUG = False
# pushs logs to console table // unicode doesn't work when debugging...
REC = True

class TwitterAPI(object):
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

    def tweet(self, status):
        """Send a tweet"""
        self.api.update_status(status=status)

    def reply(self, status, status_id):
        """Reply to a tweet"""
        self.api.update_status(status=status, in_reply_to_status_id=status_id)

ERROR_MESSAGE = [
    'You can\'t do that.',
    'That can\'t be done.',
    'Didn\'t work.',
    'Oops, can\'t do that.',
    'Sorry, you can\'t do that.',
    'That didn\'t work.',
    'Try something else.',
    'Sorry, you\'ll have to try something else.',
    'Oops, didn\'t work.',
    'Oops, try something else.',
    'Nice try, but you can\'t do that.',
    'Nice try, but that didn\'t work.',
    'Try something else, that didn\'t seem to work.'
]

if __name__ == "__main__":
    TWITTER = TwitterAPI()

    # init MENTIONS
    MENTIONS = []

    # delete console table before entering new logs
    if REC is True:
        db.delete('console', 'log', '*')

    # get latest tweets
    if DEBUG is False:
        RAW_MENTIONS = TWITTER.api.mentions_timeline(count=200)
        # get BUILDER mentions
        BUILDER = False
        for mention in RAW_MENTIONS:
            # if the account is @LiltBuilder...
            if mention.user.id == 724754312757272576:
                # and mention id is already saved to db
                if mention.id == int(
                        db.select(
                            'last_tweet_id',
                            'users',
                            'id',
                            '724754312757272576'
                        )
                    ):
                    # then skip handling this mention
                    BUILDER = True
                # if BUILDER is still false (mention not in db), let's handle this mention
                if not BUILDER:
                    MENTIONS.append({
                        'screen_name': mention.user.screen_name,
                        'user_id': mention.user.id,
                        'text': mention.text,
                        'tweet_id': mention.id
                    })
        # gets the rest of the mentions
        for mention in RAW_MENTIONS:
            mentioned = False
            mention_name = (mention.text).split(' ', 1)[0].lower()
            if mention_name != '@familiarlilt':
                mentioned = True
            for m in MENTIONS:
                # if mention is already in mentioned, or the first word in mention text isn't lilt
                if mention.user.id == m['user_id']:
                    mentioned = True
            # if user hasn't been mentioned, append it to MENTIONS
            if not mentioned:
                MENTIONS.append({
                    'screen_name': mention.user.screen_name,
                    'user_id': mention.user.id,
                    'text': mention.text,
                    'tweet_id': mention.id
                })

    # get debug tweets
    if DEBUG is True:
        db.log(REC, 'Debugging...')
        DEBUG_MENTIONS = []
        DEBUG_MENTION_ID = 1
        while db.select('screen_name', 'debug', 'tweet_id', str(DEBUG_MENTION_ID)) != None:
            DEBUG_MENTIONS.append({
                'screen_name': db.select('screen_name', 'debug', 'tweet_id', str(DEBUG_MENTION_ID)),
                'user_id': int(db.select('user_id', 'debug', 'tweet_id', str(DEBUG_MENTION_ID))),
                'text': db.select('tweet', 'debug', 'tweet_id', str(DEBUG_MENTION_ID)),
                'tweet_id': ''.join(random.choice(string.digits) for _ in range(18))
            })
            DEBUG_MENTION_ID += 1
        # go through MENTIONS from Twitter using Tweepy, gets the latest tweet from all players
        for mention in DEBUG_MENTIONS:
            try:
                mentioned = False
                mention_name = (mention['text']).split(' ', 1)[0].lower()
                if mention_name != '@familiarlilt':
                    mentioned = True
                for m in MENTIONS:
                    # if user matches user already in MENTIONS and if sent directly to Lilt
                    if mention['user_id'] == m['user_id']:
                        mentioned = True
                # if user hasn't been mentioned, append it to MENTIONS
                if mentioned is False:
                    MENTIONS.append({
                        'screen_name': mention['screen_name'],
                        'user_id': mention['user_id'],
                        'text': mention['text'],
                        'tweet_id': mention['tweet_id']
                    })
            finally:
                pass
        db.log(REC, ' ')

    db.log(REC, MENTIONS)

    BUILDER_ID = False

    # go through all MENTIONS to see which require a response from Lilt
    for mention in MENTIONS:
        try:
            user = {}
            user['screen_name'] = mention['screen_name'].lower()
            user['id'] = str(mention['user_id'])
            user['text'] = mention['text']
            user['tweet_id'] = str(mention['tweet_id'])

            reply = True if DEBUG is True else False
            cmdreply = False # these may be unnecessary
            cmd = ''

            # gets tweet user['text'] sans @familiarlilt
            # - removes @lilt_bird (or other @xxxxx) if included in tweet
            tweet = '' if len((user['text']).split()) == 1 else (user['text']).split(' ', 1)[1]
            if (tweet).split(' ', 1)[0][0] == '@':
                tweet = (tweet).split(' ', 1)[1]
            move = cleanstr(tweet)

            # converts synonyms to common word
            if move.startswith(('inspect', 'examine', 'check', 'scan')):
                move = 'look at ' + move.split(' ', 1)[1]
            elif move.startswith(('check out')):
                move = 'look at ' + move.split(' ', 2)[2]
            elif move.startswith(('grab', 'get')):
                move = 'take ' + move.split(' ', 1)[1]
            elif move.startswith(('pick up')):
                move = 'take ' + move.split(' ', 2)[2]
            elif move.startswith(('shut')):
                move = 'close ' + move.split(' ', 1)[1]

            move = move.replace('liltbluebird', 'bird')
            move = move.replace('blue bird', 'bird')
            move = move.replace('liltmerchant', 'merchant')
            move = move.replace('shopkeeper', 'merchant')
            move = move.replace('apple paste', 'paste')
            # move = move.replace(u'[emoji flower]', 'flower')
            move = move.replace(' an ', ' ')
            move = move.replace(' a ', ' ')

            # attempts to grab current user from users table
            user_exists = db.select('name', 'users', 'id', user['id'])
            if user_exists is None:
                if move == 'start':
                    db.log(REC, 'new player: ' + user['screen_name'])
                    position_init = 'start'
                    inventory_init = {}
                    events_init = {}
                    events_init[position_init] = {}
                    db.newuser(
                        user['screen_name'],
                        user['id'],
                        user['tweet_id'],
                        position_init,
                        inventory_init,
                        events_init
                    )
                    reply = True
                else:
                    # this reply is purely for debugging
                    # - since reply defaults to True, this would be redundant
                    db.log(REC, user['screen_name'] + ' isn\'t playing Lilt.')
                    reply = False
            else:
                db.log(REC, 'current player: ' + user['screen_name'])
                tweet_exists = db.select('name', 'users', 'last_tweet_id', user['tweet_id'])
                if tweet_exists is None:
                    db.log(REC, 'new tweet')
                    if user['id'] != '724754312757272576':
                        db.update(user['tweet_id'], user['id'], 'last_tweet_id')
                    elif (user['id'] == '724754312757272576') and (BUILDER_ID is False):
                        BUILDER_ID = True
                        db.update(user['tweet_id'], user['id'], 'last_tweet_id')
                    reply = True
                else:
                    db.log(REC, 'old tweet')

            # if this mention should be replied to, do so
            # might want to add double check to make sure tweet sent
            if reply:
                db.log(REC, 'tweet: ' + tweet)
                # loop through requests to users table
                user_data = ['position', 'inventory', 'events']
                for r in user_data:
                    user[r] = db.select(
                        r,
                        'users',
                        'id',
                        user['id']
                    )
                    db.log(REC, r + ': ' + str(user[r]))
                # handles commands (drop/give/inventory)
                db.log(REC, 'Checking for command...')
                cmdreply, cmd = command.get(tweet, user['inventory'], user['id'], user['position'])
                if not cmdreply:
                    # get data for db response
                    db.log(REC, 'move: ' + move)
                    # get current event (requires items from user_data)
                    user['current_event'] = event.getcurrent(
                        move,
                        user['position'],
                        user['inventory'],
                        user['events']
                    )
                    if user['current_event'] != None:
                        db.log(REC, 'current event: ' + str(user['current_event']))
                    # loop through requests to moves table (requires current_event)
                    move_data = ['response', 'item', 'drop', 'trigger', 'travel']
                    for r in move_data:
                        user[r] = db.select(
                            r,
                            'moves',
                            'move',
                            move,
                            user['position'],
                            user['current_event']
                        )
                        if user[r] != None:
                            db.log(REC, r + ': ' + str(user[r]))
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
                    db.log(REC, 'Searching...')
                    if user['response'] != None:
                        if (user['item'] != None) and (user['drop'] != None):
                            message = mbuild(
                                user['screen_name'],
                                item.replace(
                                    user['item'],
                                    user['drop'],
                                    user['inventory'],
                                    user['id'],
                                    user['response']
                                )
                            )
                        elif user['item'] != None:
                            message = mbuild(
                                user['screen_name'],
                                item.get(
                                    user['item'],
                                    user['inventory'],
                                    user['id'],
                                    user['response']
                                )
                            )
                        elif user['drop'] != None:
                            message = mbuild(
                                user['screen_name'],
                                item.drop(
                                    user['drop'],
                                    user['inventory'],
                                    user['id'],
                                    user['response']
                                )
                            )
                        else:
                            message = mbuild(user['screen_name'], user['response'])
                    else:
                        db.log(REC, 'I guess that move didn\'t work.')
                        message = mbuild(user['screen_name'], random.choice(ERROR_MESSAGE))
                        # db.log(REC, db.storeerror(move, user['position']))
                else:
                    db.log(REC, 'Command acquired, printing reply...')
                    message = mbuild(user['screen_name'], cmd)

                db.log(REC, 'reply: ' + message)
                if DEBUG is False:
                    db.log(REC, '#TweetingIt')
                    TWITTER.reply(message, user['tweet_id'])

                db.log(REC, ' ') # prints user data separate from other logs
                db.log(REC, user['screen_name'] + '\'s data: ' + str(user))
                db.log(REC, ' ')
        finally:
            pass
# db.cur.close()
# db.conn.close()
