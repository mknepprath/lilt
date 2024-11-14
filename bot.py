# -*- coding: utf-8 -*-

"""
Main bot code.
"""

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
import random
import re

# External
from openai import OpenAI
from mastodon import Mastodon

# Internal
import command
from constants import COLOR, DEBUG, ERROR_MESSAGES, MKNEPPRATH
import db
import event
import item
from utils import normalize_post, build_tweet


client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


class HTMLFilter(HTMLParser):
    text = ""

    def handle_data(self, data):
        self.text += data


def openai_transform(move):
    """
    Takes a move and returns a transformed move that the game can understand.
    """
    prompt = "Example commands: 'inspect X', 'use X on Y', 'open X', 'pick up X', 'go to X', 'eat X', 'drink X', " \
             "'talk to X', 'look around', 'look in X', 'look right', 'check inventory', etc. to play the " \
             "game. Translate the following into a command: " + move + ". Command:"

    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt
                }
            ],
            model="gpt-4",
        )
    except Exception as e:
        print("Error:", str(e))
        return None

    print(response)
    text = response.choices[0].message.content
    text = re.split('; | // |, |\. |\*|\n', text)[0]
    move = normalize_post(text)

    return move


def main():
    mastodon = Mastodon(
        api_base_url='https://botsin.space',
        client_id=os.environ.get('MASTODON_CLIENT_KEY'),
        client_secret=os.environ.get('MASTODON_CLIENT_SECRET'),
        access_token=os.environ.get('MASTODON_ACCESS_TOKEN'),
    )

    # Initialize mentions.
    mentions = []

    # Get the latest 200 mentions.
    raw_mentions = mastodon.notifications(limit=100, types=["mention"])

    # Gets the rest of the mentions.
    for mention in raw_mentions:
        # Default to not skip post.
        skip_tweet = False

        # If the post is greater than 3 days, skip it.
        if (datetime.now(timezone.utc) - mention.created_at).days > 3:
            skip_tweet = True

        # TODO: I could be smarter here? mention.entities['user_mentions'])
        # TODO: Allow replies to self. It happens.
        # if not skip_tweet and mention.status.mentions != LILT:
        # if not skip_tweet and [m for m in mention.status.mentions if m.id == LILT]:
        #     print("❌ not in reply to lilt")
        #     skip_tweet = True

        # While debugging, ignore tweets by other players.
        if not skip_tweet and DEBUG.BOT and mention.account.id != MKNEPPRATH:
            print("❌ Skipping non-@mknepprath tweets while debugging.",
                  (datetime.now(timezone.utc) - mention.created_at).days)
            skip_tweet = True

        # Check currently aggregated mentions to see if we've already
        # found a post by this player.
        if not skip_tweet:
            for m in mentions:
                # If mention is already in skip_tweet.
                if mention.account.id == m['user_id']:
                    skip_tweet = True
                    break

        # If the skip_tweet flag hasn't been set to True, append post to
        # mentions.
        if not skip_tweet:
            print('=> @{name}: {text}'.format(
                name=mention.account.acct, text=mention.status.content))

            f = HTMLFilter()
            f.feed(mention.status.content)

            mentions.append({
                'screen_name': mention.account.acct,
                'user_id': mention.account.id,
                'text': f.text,
                'tweet_id': mention.status.id,
                'visibility': mention.status.visibility
            })

    print(' ')

    # Go through all mentions to see which require a response from Lilt.
    for mention in mentions:
        try:
            # unsafe_user serves no purpose beyond being a data dumping ground.
            # Can be smarter about this.
            unsafe_user = {
                'screen_name': mention['screen_name'].lower(),
                'id': mention['user_id'],
                'text': mention['text'],
                'tweet_id': mention['tweet_id'],
                'visibility': mention['visibility']
            }

            reply = False

            # gets post unsafe_user['text'] sans @lilt - removes @lilt_bird (or other @xxxxx) if included in
            # post
            post = '' if len((unsafe_user['text']).split()) == 1 else (
                unsafe_user['text']).split(' ', 1)[1]

            # If the post begins with a screen_name, remove it.
            if post[0][0] == '@':
                post = post.split(' ', 1)[1]

            # If a player includes any text after a semicolon, double slash,
            # comma, period, or star, ignore it.
            post = re.split('; | // |, |\. |\*|\n', post)[0]
            move = normalize_post(post)

            # Attempts to fetch the player data from users table.
            user_exists = db.select('name', 'users', 'id', unsafe_user['id'])

            # If none is found, check intent.
            if user_exists is None:
                # If the post says "start," a new player is added.
                if move == 'start':
                    print('New player: ' + unsafe_user['screen_name'] + '.')

                    # Should reply to new players.
                    reply = True

                    db.create_new_user(
                        unsafe_user['screen_name'],
                        unsafe_user['id'],
                        unsafe_user['tweet_id']
                    )
                else:
                    # Otherwise, they mentioned Lilt and aren't playing.
                    print(unsafe_user['screen_name'] + ' isn\'t playing Lilt.')
                    print(' ')
            else:
                print('Current player: ' + unsafe_user['screen_name'] + '.')

                # This is a current player, check if the bot has already
                # replied to this post.
                tweet_exists = db.select(
                    'name', 'users', 'last_tweet_id', unsafe_user['tweet_id'])

                if tweet_exists is None:
                    print('New post. I will reply.')

                    # If the post ID doesn't match the last one saved, the bot
                    # should reply.
                    reply = True

                    # Save this post ID so we can compare to it next time the
                    # bot checks.
                    # TODO: It's dangerous to update this before replying to the post.
                    if DEBUG.BOT:
                        print(
                            COLOR.WARNING + 'Not saving last_tweet_id while debugging.' + COLOR.END)
                    else:
                        print(
                            COLOR.GREEN + 'Saving post as last_tweet_id.' + COLOR.END)
                        db.update_user(unsafe_user['tweet_id'],
                                       unsafe_user['id'], 'last_tweet_id')
                else:
                    # Bot already replied to this post.
                    print('Old post.')
                    print(' ')

            # If this mention should be replied to, do so.
            # TODO: Might want to add double-check to make sure the post sent.
            if reply:
                print('Normalized post: ' + move)

                # TODO: Feels like all of this could be a bit more concise. Can
                #  we make fewer calls to the database for this information?

                # Get the player's position.
                unsafe_user['position'] = db.select(
                    'position', 'users', 'id', unsafe_user['id'])

                # Get the player's inventory.
                unsafe_user['inventory'] = db.select(
                    'inventory', 'users', 'id', unsafe_user['id'])

                # Get the player's state.
                unsafe_user['events'] = json.loads(
                    db.select('events', 'users', 'id', unsafe_user['id']))

                unsafe_user, message = parse_move(unsafe_user, move)

                if unsafe_user['response'] is None and message is None:
                    # attempt to transform move with openai
                    print('Starting OpenAI translation...')
                    unsafe_user, message = parse_move(unsafe_user, openai_transform(move))

                # If there is still no valid response,
                if unsafe_user['response'] is None and message is None:
                    # No response was found. Return an error message.
                    print('That move didn\'t work.')
                    message = build_tweet(
                        unsafe_user['screen_name'], random.choice(ERROR_MESSAGES))
                else:
                    # If a change was triggered, such as "chest: closed", add
                    # that change to player state for their current location.
                    if unsafe_user['trigger'] is not None:
                        # Converts the trigger property to JSON.
                        unsafe_user['trigger'] = json.loads(
                            unsafe_user['trigger'])

                        # Updates the player's position with the updated state.
                        unsafe_user['events'][unsafe_user['position']].update(
                            unsafe_user['trigger'])

                        # Saves change to database.
                        if DEBUG.BOT:
                            print(
                                COLOR.WARNING + 'Not saving state changes while debugging.' + COLOR.END)
                        else:
                            print(
                                COLOR.GREEN + 'Saving state changes.' + COLOR.END)
                            db.update_user(unsafe_user['events'],
                                           unsafe_user['id'], 'events')

                    # If the player is traveling, move them and add new location
                    #  to state.
                    if unsafe_user['travel'] is not None:
                        # Save position to database.
                        if DEBUG.BOT:
                            print(
                                COLOR.WARNING + 'Not updating position while debugging.' + COLOR.END)
                        else:
                            print(COLOR.GREEN +
                                  'Updating position.' + COLOR.END)
                            db.update_user(unsafe_user['travel'],
                                           unsafe_user['id'], 'position')

                        # If the position doesn't exist in player state yet...
                        if unsafe_user['travel'] not in unsafe_user['events']:
                            # Initialize the position in state (events).
                            unsafe_user['events'][unsafe_user['travel']] = {}

                            # Save state (events) to database.
                            if DEBUG.BOT:
                                print(
                                    COLOR.WARNING + 'Not adding position to state while debugging.' + COLOR.END)
                            else:
                                print(
                                    COLOR.GREEN + 'Adding position to state.' + COLOR.END)
                                db.update_user(
                                    unsafe_user['events'], unsafe_user['id'], 'events')

                    # Get a response.
                    print('Handle any inventory changes and respond.')

                    if unsafe_user['response'] is not None:
                        # These item functions are essentially pass-throughs for
                        # the response unless there's an issue with the player's
                        # inventory.

                        # The player is updating an item, so we must remove the
                        #  old item and replace with the new version of it.
                        if (unsafe_user['item'] is not None) and (unsafe_user['drop'] is not None):
                            print('Let\'s replace ' +
                                  unsafe_user['drop'] + ' with ' + unsafe_user['item'] + '.')
                            message = build_tweet(unsafe_user['screen_name'], item.replace(
                                unsafe_user['drop'], unsafe_user['item'], unsafe_user['inventory'], unsafe_user['id'],
                                unsafe_user['response']))

                        # The player is getting a new item.
                        elif unsafe_user['item'] is not None:
                            message = build_tweet(unsafe_user['screen_name'], item.get(
                                unsafe_user['item'], unsafe_user['inventory'], unsafe_user['id'],
                                unsafe_user['response']))

                        # The player is dropping an item.
                        elif unsafe_user['drop'] is not None:
                            message = build_tweet(unsafe_user['screen_name'], item.drop(
                                unsafe_user['drop'], unsafe_user['inventory'], unsafe_user['id'],
                                unsafe_user['response']))

                        # We're not modifying the inventory. Return the response.
                        else:
                            message = build_tweet(
                                unsafe_user['screen_name'], unsafe_user['response'])

                print('Replying with, "{message}"'.format(message=message))
                if DEBUG.BOT:
                    print(
                        COLOR.WARNING + 'Not tweeting while debugging.' + COLOR.END)
                else:
                    print(
                        COLOR.GREEN + 'Tooting.' + COLOR.END)
                    mastodon.status_post(
                        status=message,
                        in_reply_to_id=unsafe_user['tweet_id'],
                        visibility=unsafe_user['visibility']
                    )

                print(' ')
                print(unsafe_user['screen_name'] +
                      '\'s dump: ' + str(unsafe_user))
                print(' ')
        except:
            pass


def parse_move(unsafe_user, move):
    # Handles commands (drop/give/inventory). Also @LiltBuilder
    #  queries. TODO: How this is being handled ain't great.
    print('Checking if this is a command post...')
    command_message = command.get(
        move, unsafe_user['inventory'], unsafe_user['id'], unsafe_user['position'])
    # If there was a message returned above, I can assume this is
    # a "command" move. Need a better name for this. Command move
    # responses are generated, not queried from the database.
    if len(command_message) != 0:
        print('Command acquired, printing reply...')

        # This is the completed message that will be sent. Can skip
        # most of what's below.
        message = build_tweet(
            unsafe_user['screen_name'], command_message)

        print('Replying with, "{message}"'.format(message=message))

        return unsafe_user, message
    else:
        print('Did not receive a command message. Not a command post.')
        # This is it. Time to figure out what the correct response
        # is for this post.
        print('Move:', "'" + move + "'")

        # Get current event that applies to this move (requires
        # items from unsafe_user). This is because the inventory is being
        # added to state ("events").
        unsafe_user['current_event'] = event.get_current_event(
            move, unsafe_user['position'], unsafe_user['inventory'], unsafe_user['events'])

        # Loop through requests to moves table (requires
        # current_event). TODO: Would make more sense to use *...
        move_data = ['response', 'item',
                     'drop', 'trigger', 'travel']
        for move_property in move_data:
            # Given the move and current state, get the above "move
            #  data". TODO: I'm assigning this to the unsafe_user dict -
            #          seems messy.
            unsafe_user[move_property] = db.select(
                move_property, 'moves', 'move', move, unsafe_user['position'], unsafe_user['current_event'])
            if unsafe_user[move_property] is not None:
                print('For ' + move_property + ', \'' +
                      str(unsafe_user[move_property]) + '\'.')

        return unsafe_user, None


# db.cur.close()
# db.conn.close()


if __name__ == "__main__":
    main()
