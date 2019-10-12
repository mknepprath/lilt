# -*- coding: utf-8 -*-

"""
Main bot code.
"""

# External
from datetime import datetime
import json
import os
import random
import string
import tweepy

# Internal
import command
from constants import COLOR, DEBUG, ERROR_MESSAGES, FAMILIARLILT, LILTBUILDER, MKNEPPRATH
import db
import event
import item
from utils import filter_tweet, build_tweet, build_inventory_tweet


class TwitterAPI:
    """
    Class for accessing the Twitter API.
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
        # Send a tweet.
        self.api.update_status(status=message)

    def reply(self, message, tweet_id):
        # Reply to a tweet.
        self.api.update_status(status=message, in_reply_to_status_id=tweet_id)


if __name__ == "__main__":
    twitter = TwitterAPI()

    # Initialize mentions.
    mentions = []

    # Get the latest 200 mentions.
    raw_mentions = twitter.api.mentions_timeline(count=200)

    # Get LiltBuilder mentions.
    stop_collecting_builder_tweets = False
    for mention in raw_mentions:
        if mention.user.id_str == LILTBUILDER:
            # Checks the last recorded tweet ID by LiltBuilder. If the
            # current mention ID matches the last recorded, stop collecting
            # LiltBuilder tweets.
            if mention.id_str == int(db.select('last_tweet_id', 'users', 'id', LILTBUILDER)):
                stop_collecting_builder_tweets = True
            # If we're still collectin builder tweets, add it to the
            # mentions list.
            # TODO: We're adding this to the same list as other mentions,
            # which seems odd. Consider handling separately.
            if stop_collecting_builder_tweets == False:
                mentions.append({
                    'screen_name': mention.user.screen_name,
                    'user_id': mention.user.id_str,
                    'text': mention.text,
                    'tweet_id': mention.id_str
                })

    # Gets the rest of the mentions.
    for mention in raw_mentions:
        # Default to not skip tweet.
        skip_tweet = False

        # If the tweet is greater than 3 days, skip it.
        if (datetime.now() - mention.created_at).days > 3:
            skip_tweet = True

        # TODO: I could be smarter here? mention.entities['user_mentions'])
        # TODO: Allow replies to self. It happens.
        if not skip_tweet and mention.in_reply_to_user_id_str != FAMILIARLILT:
            skip_tweet = True

        # While debugging, ignore tweets by other players.
        if not skip_tweet and DEBUG.BOT and mention.user.id_str != MKNEPPRATH:
            print('Skipping non-@mknepprath tweets while debugging.',
                  (datetime.now() - mention.created_at).days)
            skip_tweet = True

        # Check currently aggregated mentions to see if we've already
        # found a tweet by this player.
        if not skip_tweet:
            for m in mentions:
                # If mention is already in skip_tweet.
                if mention.user.id_str == m['user_id']:
                    skip_tweet = True
                    break

        # If the skip_tweet flag hasn't been set to True, append tweet to
        # mentions.
        if not skip_tweet:
            print('=> @{name}: {text}'.format(
                name=mention.user.screen_name, text=mention.text))

            mentions.append({
                'screen_name': mention.user.screen_name,
                'user_id': mention.user.id_str,
                'text': mention.text,
                'tweet_id': mention.id_str
            })

    print(' ')

    # Go through all mentions to see which require a response from Lilt.
    for mention in mentions:
        try:
            # user_UNSAFE serves no purpose beyond being a data dumping ground.
            # Can be smarter about this.
            user_UNSAFE = {}
            user_UNSAFE['screen_name'] = mention['screen_name'].lower()
            user_UNSAFE['id'] = mention['user_id']
            user_UNSAFE['text'] = mention['text']
            user_UNSAFE['tweet_id'] = mention['tweet_id']

            reply = False

            command_message = ''

            # gets tweet user_UNSAFE['text'] sans @familiarlilt - removes @lilt_bird (or other @xxxxx) if included in tweet
            tweet = '' if len((user_UNSAFE['text']).split()) == 1 else (
                user_UNSAFE['text']).split(' ', 1)[1]

            # If the tweet begins with a screen_name, remove it.
            if tweet[0][0] == '@':
                tweet = (tweet).split(' ', 1)[1]

            # If a player includes any text after '//', ignore it.
            tweet = tweet.split('//')[0]

            move = filter_tweet(tweet)

            # Converts synonyms to common word.
            # TODO: Move to filter_tweet? This is doing similar things.
            # 'check out' has to be first, otherwise 'check' gets removed by the
            # next replace.
            if move.startswith(('check out')):
                move = 'look at ' + move.split(' ', 2)[2]
            elif move.startswith(('inspect', 'examine', 'check', 'scan')):
                move = 'look at ' + move.split(' ', 1)[1]
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
            move = move.replace(u'🌺', 'flower')
            move = move.replace(' an ', ' ')
            move = move.replace(' a ', ' ')

            # Attempts to fetch the player data from users table.
            user_exists = db.select('name', 'users', 'id', user_UNSAFE['id'])

            # If none is found, check intent.
            if user_exists == None:
                # If the tweet says "start," a new player is added.
                if move == 'start':
                    print('New player: ' + user_UNSAFE['screen_name'] + '.')

                    # Should reply to new players.
                    reply = True

                    db.create_new_user(
                        user_UNSAFE['screen_name'],
                        user_UNSAFE['id'],
                        user_UNSAFE['tweet_id']
                    )
                else:
                    # Otherwise, they mentioned Lilt and aren't playing.
                    print(user_UNSAFE['screen_name'] + ' isn\'t playing Lilt.')
                    print(' ')
            else:
                print('Current player: ' + user_UNSAFE['screen_name'] + '.')

                # This is a current player, check if the bot has already
                # replied to this tweet.
                tweet_exists = db.select(
                    'name', 'users', 'last_tweet_id', user_UNSAFE['tweet_id'])

                if tweet_exists == None:
                    print('New tweet. I will reply.')

                    # If the tweet ID doesn't match the last one saved, the bot
                    # should reply.
                    reply = True

                    # Save this tweet ID so we can compare to it next time the
                    # bot checks.
                    # TODO: It's dangerous to update this before replying to the
                    # tweet.
                    if DEBUG.BOT:
                        print(
                            COLOR.WARNING + 'Not saving last_tweet_id while debugging.' + COLOR.END)
                    else:
                        print(
                            COLOR.GREEN + 'Saving tweet as last_tweet_id.' + COLOR.END)
                        db.update_user(user_UNSAFE['tweet_id'],
                                       user_UNSAFE['id'], 'last_tweet_id')
                else:
                    # Bot already replied to this tweet.
                    print('Old tweet.')
                    print(' ')

            # If this mention should be replied to, do so.
            # TODO: Might want to add double-check to make sure the tweet sent.
            if reply == True:
                print('Tweet: ' + tweet)

                # TODO: Feels like all of this could be a bit more concise. Can
                # we make fewer calls to the database for this information?

                # Get the player's position.
                user_UNSAFE['position'] = db.select(
                    'position', 'users', 'id', user_UNSAFE['id'])

                # Get the player's inventory.
                user_UNSAFE['inventory'] = db.select(
                    'inventory', 'users', 'id', user_UNSAFE['id'])

                # Get the player's state.
                user_UNSAFE['events'] = json.loads(
                    db.select('events', 'users', 'id', user_UNSAFE['id']))

                # Handles commands (drop/give/inventory). Also @LiltBuilder
                # queries. TODO: How this is being handled ain't great.
                print('Checking if this is a command tweet...')
                command_message = command.get(
                    tweet, user_UNSAFE['inventory'], user_UNSAFE['id'], user_UNSAFE['position'])

                # If there was a message returned above, I can assume this is
                # a "command" move. Need a better name for this. Command move
                # responses are generated, not queried from the database.
                if len(command_message) != 0:
                    print('Command acquired, printing reply...')

                    # This is the completed message that will be sent. Can skip
                    # most of what's below.
                    message = build_tweet(
                        user_UNSAFE['screen_name'], command_message)
                else:
                    print('Did not receive a command message. Not a command tweet.')
                    # This is it. Time to figure out what the correct response
                    # is for this tweet.
                    print('Move:', move)

                    # Get current event that applies to this move (requires
                    # items from user_UNSAFE). This is because the inventory is being
                    # added to state ("events").
                    user_UNSAFE['current_event'] = event.get_current_event(
                        move, user_UNSAFE['position'], user_UNSAFE['inventory'], user_UNSAFE['events'])

                    # Loop through requests to moves table (requires
                    # current_event). TODO: Would make more sense to use *...
                    move_data = ['response', 'item',
                                 'drop', 'trigger', 'travel']
                    for move_property in move_data:
                        # Given the move and current state, get the above "move
                        # data". TODO: I'm assigning this to the user_UNSAFE dict -
                        # seems messy.
                        user_UNSAFE[move_property] = db.select(
                            move_property, 'moves', 'move', move, user_UNSAFE['position'], user_UNSAFE['current_event'])
                        if user_UNSAFE[move_property] != None:
                            print('For ' + move_property + ', \'' +
                                  str(user_UNSAFE[move_property]) + '\'.')

                    # If a change was triggered, such as "chest: closed", add
                    # that change to player state for their current location.
                    if user_UNSAFE['trigger'] != None:
                        # Converts the trigger property to JSON.
                        user_UNSAFE['trigger'] = json.loads(
                            user_UNSAFE['trigger'])

                        # Updates the player's position with the updated state.
                        user_UNSAFE['events'][user_UNSAFE['position']].update(
                            user_UNSAFE['trigger'])

                        # Saves change to database.
                        if DEBUG.BOT:
                            print(
                                COLOR.WARNING + 'Not saving state changes while debugging.' + COLOR.END)
                        else:
                            print(
                                COLOR.GREEN + 'Saving state changes.' + COLOR.END)
                            db.update_user(user_UNSAFE['events'],
                                           user_UNSAFE['id'], 'events')

                    # If the player is traveling, move them and add new location
                    # to state.
                    if user_UNSAFE['travel'] != None:
                        # Save position to database.
                        if DEBUG.BOT:
                            print(
                                COLOR.WARNING + 'Not updating position while debugging.' + COLOR.END)
                        else:
                            print(COLOR.GREEN +
                                  'Updating position.' + COLOR.END)
                            db.update_user(user_UNSAFE['travel'],
                                           user_UNSAFE['id'], 'position')

                        # If the position doesn't exist in player state yet...
                        if user_UNSAFE['travel'] not in user_UNSAFE['events']:
                            # Initialize the position in state (events).
                            user_UNSAFE['events'][user_UNSAFE['travel']] = {}

                            # Save state (events) to database.
                            if DEBUG.BOT:
                                print(
                                    COLOR.WARNING + 'Not adding position to state while debugging.' + COLOR.END)
                            else:
                                print(
                                    COLOR.GREEN + 'Adding position to state.' + COLOR.END)
                                db.update_user(
                                    user_UNSAFE['events'], user_UNSAFE['id'], 'events')

                    # Get a response.
                    print('Handle any inventory changes and respond.')

                    if user_UNSAFE['response'] != None:
                        # These item functions are essentially pass-throughs for
                        # the response unless there's an issue with the player's
                        # inventory.

                        # The player is updating an item, so we must remove the
                        # old item and replace with the new version of it.
                        if (user_UNSAFE['item'] != None) and (user_UNSAFE['drop'] != None):
                            print('Let\'s replace ' +
                                  user_UNSAFE['drop'] + ' with ' + user_UNSAFE['item'] + '.')
                            message = build_tweet(user_UNSAFE['screen_name'], item.replace(
                                user_UNSAFE['drop'], user_UNSAFE['item'], user_UNSAFE['inventory'], user_UNSAFE['id'], user_UNSAFE['response']))

                        # The player is getting a new item.
                        elif user_UNSAFE['item'] != None:
                            message = build_tweet(user_UNSAFE['screen_name'], item.get(
                                user_UNSAFE['item'], user_UNSAFE['inventory'], user_UNSAFE['id'], user_UNSAFE['response']))

                        # The player is dropping an item.
                        elif user_UNSAFE['drop'] != None:
                            message = build_tweet(user_UNSAFE['screen_name'], item.drop(
                                user_UNSAFE['drop'], user_UNSAFE['inventory'], user_UNSAFE['id'], user_UNSAFE['response']))

                        # We're not modifying the inventory. Return the response.
                        else:
                            message = build_tweet(
                                user_UNSAFE['screen_name'], user_UNSAFE['response'])
                    else:
                        # No response was found. Return an error message.
                        print('That move didn\'t work.')
                        message = build_tweet(
                            user_UNSAFE['screen_name'], random.choice(ERROR_MESSAGES))

                print('Replying with, "{message}"'.format(message=message))
                if DEBUG.BOT:
                    print(
                        COLOR.WARNING + 'Not tweeting while debugging.' + COLOR.END)
                else:
                    print(
                        COLOR.GREEN + 'Tweeting.' + COLOR.END)
                    twitter.reply(message, user_UNSAFE['tweet_id'])

                print(' ')
                print(user_UNSAFE['screen_name'] +
                      '\'s dump: ' + str(user_UNSAFE))
                print(' ')
        except:
            pass

# db.cur.close()
# db.conn.close()
