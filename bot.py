import os
import time
import string
import random
import tweepy
import psycopg2
import urlparse
import json

# debugging options
debug = True
delete_tweets = False

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

    def reply(self, message, tweetid):
        """Reply to a tweet"""
        self.api.update_status(status=message, in_reply_to_status_id=tweetid)

def getitem(item, response):
    # update values here: items, triggers, etc
    if item not in inventory:
        inventory[item] = {}
        inventory[item]['quantity'] = 1
        # check if there's room in the inventory
        if len(invbuilder(inventory, 'x'*15)) >= 140:
            return '@' + screen_name + ' Your inventory is full. ' + randstring
        else:
            # update database with updated values
            cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
            conn.commit()
            # formulate reply message and print it to the console
            return '@' + screen_name + ' ' + response + ' ' + randstring
    else:
        cur.execute("SELECT max FROM items WHERE name = %s;", (str(item),))
        item_max = cur.fetchone()
        if inventory[item]['quantity'] < item_max[0]:
            inventory[item]['quantity'] += 1
            # check if there's room in the inventory
            if len(invbuilder(inventory, 'x'*15)) >= 140:
                return '@' + screen_name + ' Your inventory is full. ' + randstring
            else:
                # update database with updated values
                cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
                conn.commit()
                # formulate reply message and print it to the console
                return '@' + screen_name + ' ' + response + ' ' + randstring
        else:
            # formulate reply message and print it to the console
            return '@' + screen_name + ' You can\'t hold more ' + item + '! ' + randstring

def dropitem(item):
    if item not in inventory:
        return '@' + screen_name + ' You don\'t have anything like that. ' + randstring
        print "reply: " + message
    elif inventory[item]['quantity'] <= 1:
        del inventory[item]
        cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
        conn.commit()
        return '@' + screen_name + ' You drop one ' + item + '.' + randstring
        print "reply: " + message
    else:
        inventory[item]['quantity'] -= 1
        cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id),))
        conn.commit()
        return '@' + screen_name + ' You drop one ' + item + '.' + randstring

def giveitem(item, recipient):
    print 'so you want to give ' + item + ' to ' + recipient #TESTING
    # update values here: items, triggers, etc
    if item not in inventory:
        print item + ' wasn\'t in the inventory' #TESTING
        return '@' + screen_name + ' You don\'t have ' + item + '! ' + randstring
    else:
        print 'okay so you do have the item' #TESTING
        #check if item can be given
        cur.execute("SELECT give FROM items WHERE name = %s;", (str(item),))
        givable = cur.fetchone()
        print 'givableness of item should be above this...'
        if givable[0] == False:
            print 'cant give that away!'
            return '@' + screen_name + ' ' + item.capitalize() + ' can\'t be given. ' + randstring
        else:
            #check if recipient exists
            cur.execute("SELECT id FROM users WHERE name = %s;", (str(recipient),))
            recipient_id = cur.fetchone()
            if recipient_id == None:
                print 'ya that person doesn\'t exist' #TESTING
                return '@' + screen_name + ' They aren\'t playing Lilt! ' + randstring
            else:
                # get recipient inventory
                cur.execute("SELECT inventory FROM users WHERE name = %s;", (str(recipient),))
                inv = cur.fetchone()
                print 'got the inventory for recipient I think' #TESTING
                # might be better to have a default value in users, but this checks to see if empty and creates dict if it is
                if (inv == None) or (inv[0] == None):
                    recipient_inventory = {}
                    print 'their inventory was empty so created an empty json deal' #TESTING
                else:
                    recipient_inventory = json.loads(inv[0])
                print 'got tha recipients inventory' #TESTING
                # modify recipient inventory, see if it fits
                if item not in recipient_inventory:
                    print 'oh ya they dind\'t have that item'
                    recipient_inventory[item] = {}
                    recipient_inventory[item]['quantity'] = 1
                    if inventory[item]['quantity'] <= 1:
                        del inventory[item]
                    else:
                        inventory[item]['quantity'] -= 1
                    # check if there's room in the inventory
                    if len(invbuilder(recipient_inventory, 'x'*15)) >= 140:
                        print 'hmm yup they couldn\'t hold anything else' #TESTING
                        return '@' + screen_name + ' Their inventory is full. ' + randstring
                    else:
                        # update database with updated values
                        print 'alright so they should be able to hold this item' #TESTING
                        cur.execute("UPDATE users SET inventory = %s WHERE name = %s;", (json.dumps(recipient_inventory), str(recipient),))
                        conn.commit()
                        cur.execute("UPDATE users SET inventory = %s WHERE id = %s", (json.dumps(inventory), str(user_id)))
                        conn.commit()
                        # formulate reply message and print it to the console
                        print 'now they got it' #TESTING
                        return '@' + screen_name + ' You gave ' + item + ' to @' + recipient + '. ' + randstring
                else:
                    #they've got the item already, so we have to make sure they can accept more
                    cur.execute("SELECT max FROM items WHERE name = %s;", (str(item),))
                    item_max = cur.fetchone()
                    print 'I think the item max has been grabbed hopefully... we\'ll see' #TESTING
                    if recipient_inventory[item]['quantity'] < item_max[0]:
                        print 'shuld be room in that inventory for the item' #TESTING
                        recipient_inventory[item]['quantity'] += 1
                        if inventory[item]['quantity'] <= 1:
                            del inventory[item]
                        else:
                            inventory[item]['quantity'] -= 1
                        # check if there's room in the inventory
                        if len(invbuilder(recipient_inventory, 'x'*15)) >= 140:
                            return '@' + screen_name + ' Their inventory is full. ' + randstring
                        else:
                            print 'update the database with inventory stuff cuz it\'s all gud' #TESTING
                            # update database with updated values
                            cur.execute("UPDATE users SET inventory = %s WHERE name = %s;", (json.dumps(recipient_inventory), str(recipient)))
                            conn.commit()
                            cur.execute("UPDATE users SET inventory = %s WHERE id = %s;", (json.dumps(inventory), str(user_id)))
                            conn.commit()
                            # formulate reply message and print it to the console
                            return '@' + screen_name + ' You gave ' + item + ' to @' + recipient + '. ' + randstring
                    else:
                        # formulate reply message and print it to the console
                        return '@' + screen_name + ' They can\'t hold more ' + item + '! ' + randstring

def invbuilder(inventory, screen_name):
    items = list(inventory.keys())
    i = 0
    while i < len(items):
        iq = inventory[items[i]]['quantity'] # item quantity (items[i] would resolve to item's name)
        if iq > 1: # only append quantity info if more than one
            items[i] += ' ' + u'\u2022'*iq
        i += 1
    return '@' + screen_name + ' ' + ', '.join(items)

if __name__ == "__main__":
    twitter = TwitterAPI()

    # deletes all tweets so far
    if delete_tweets == True:
        for status in tweepy.Cursor(twitter.api.user_timeline).items():
            try:
                print status.text
                twitter.api.destroy_status(status.id)
            except:
                pass

    # init mentions
    mentions = []

    # mentions for testing purposes
    if debug == True:
        mentions.append({
            'screen_name': 'mknepprath',
            'user_id': 15332057,
            'tweet': 'close chest', # update this with tweet to test
            'tweetid': 703619369989853172
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
                        'tweetid': mention.id
                    })

            except:
                pass

    # go through all mentions that require a response from Lilt
    for mention in mentions:
        try:
            screen_name = mention['screen_name']
            user_id = mention['user_id']
            tweet = mention['tweet']
            tweetid = mention['tweetid']
            reply = False

            # attempts to grab current user from users table
            cur.execute("""SELECT 1 FROM users WHERE id = %s;""", (str(user_id),))
            user_exists = cur.fetchone()
            # if they're in the table, grab tweet id from table
            if user_exists != None:
                print "current player: " + screen_name
                cur.execute("""SELECT 1 FROM users WHERE last_tweet_id = %s;""", (str(tweetid),))
                tweet_exists = cur.fetchone()
                # if tweetid isn't in users table, update tweetid
                if tweet_exists == None:
                    print "new tweet"
                    cur.execute("UPDATE users SET last_tweet_id = %s WHERE id = %s;", (tweetid, str(user_id)))
                    reply = True
                    conn.commit()
                # otherwise, do nothing - tweet has already been replied to
                else:
                    print "old tweet"
            else:
                # if user is not in the users table, add user and tweetid
                print "new player: " + screen_name
                cur.execute("INSERT INTO users (name, id, last_tweet_id) VALUES (%s, %s, %s)", (screen_name, user_id, tweetid))
                reply = True
                conn.commit()

            # when debugging, always reply (even if tweet id is the same)
            if debug == True:
                reply = True

            # might want to add double check to make sure tweet sent
            # if this mention should be replied to, do so
            if reply == True:
                print "tweet: " + tweet

                # removes punctuation and makes move lowercase
                exclude = set(string.punctuation) # using this later, as well - maybe init at beginning?
                move = ''.join(ch for ch in tweet if ch not in exclude).lower()
                print "move: " + move

                # get position
                cur.execute("SELECT position FROM users WHERE id = %s;", (str(user_id),))
                pos = cur.fetchone()
                position = pos[0]
                print "position: " + position

                # get inventory
                cur.execute("SELECT inventory FROM users WHERE id = %s;", (str(user_id),))
                inv = cur.fetchone()
                # might be better to have a default value in users, but this checks to see if empty and creates dict if it is
                if (inv == None) or (inv[0] == None):
                    inventory = {}
                else:
                    inventory = json.loads(inv[0])
                print "inventory: " + str(inventory)

                # get events
                cur.execute("SELECT events FROM users WHERE id = %s;", (str(user_id),))
                ev = cur.fetchone()
                # might be better to have a default value in users, but this checks to see if empty and creates dict if it is
                if (ev == None) or (ev[0] == None):
                    events = {}
                else:
                    events = json.loads(ev[0])
                    events_and_items = json.loads(ev[0])
                print "events: " + str(events)

                items = list(inventory.keys())
                for item in items:
                    events_and_items[position][item] = 'inventory'
                print "events_and_items: " + str(events_and_items)

                condition_response = False
                current_event = {}
                # loop through move/event combos to see if a condition matches
                for key, value in events_and_items[position].iteritems():
                    try:
                        event = {}
                        # assign current event to event
                        event[key] = value
                        print "event: " + str(event)
                        # check if there is a response for this move when condition is met (this event)
                        cur.execute("SELECT response FROM moves WHERE move = %s AND position = %s AND condition = %s;", (str(move),str(position),json.dumps(event)))
                        response = cur.fetchone()
                        if response != None:
                            condition_response = True
                            current_event = event
                            pass
                    except:
                        pass

                print "current event: " + str(current_event)

                # get response
                if condition_response == True:
                    cur.execute("SELECT response FROM moves WHERE move = %s AND position = %s AND condition = %s;", (str(move),str(position),json.dumps(current_event)))
                else:
                    cur.execute("SELECT response FROM moves WHERE move = %s AND position = %s;", (str(move),str(position)))
                response = cur.fetchone()
                print "response: " + str(response)

                # get item (if one exists)
                if condition_response == True:
                    cur.execute("SELECT item FROM moves WHERE move = %s AND position = %s AND condition = %s;", (str(move),str(position),json.dumps(current_event)))
                else:
                    cur.execute("SELECT item FROM moves WHERE move = %s AND position = %s;", (str(move),str(position)))
                newitem = cur.fetchone()
                print "item: " + str(newitem)

                # get trigger for move and add it to events
                if condition_response == True:
                    cur.execute("SELECT trigger FROM moves WHERE move = %s AND position = %s AND condition = %s;", (str(move),str(position),json.dumps(current_event)))
                else:
                    cur.execute("SELECT trigger FROM moves WHERE move = %s AND position = %s;", (str(move),str(position)))
                trig = cur.fetchone()
                # if there is a trigger, add it
                if (trig != None) and (trig[0] != None):
                    trigger = json.loads(trig[0])
                    print "trigger: " + str(trigger)
                    if position not in events:
                        # add position dict item to events if it's not there yet
                        events[position] = {}
                    # add trigger to events (this adds or updates current value at key of trigger)
                    events[position].update(trigger)
                    cur.execute("UPDATE users SET events = %s WHERE id = %s;", (json.dumps(events), str(user_id),))
                    conn.commit()
                print "events: " + str(events)

                # randstring to avoid Twitter getting mad about duplicate tweets // should think up a better solution for this
                randstring = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

                # if tweet is two words or more, break off first word
                if len((tweet).split()) >= 2:
                    a, b = (tweet).split(' ',1)
                    a = ''.join(ch for ch in a if ch not in exclude).lower()
                    # if first word is drop - a is the move, b is the item
                    # this has to be nested or inventory doesn't work... not sure why
                    if (a == 'drop'):
                        move = a
                        item = ''.join(ch for ch in b if ch not in exclude).lower()
                    # if first word is give - break apart b
                    elif (a == 'give'):
                        move = a
                        # c will be the item, and b should be the recipient
                        c, d = (b).split(' ',1)
                        recipient = ''.join(ch for ch in c if ch not in exclude).lower()
                        item = ''.join(ch for ch in d if ch not in exclude).lower()

                # logic that generates response to player's move
                if move == 'drop':
                    message = dropitem(item)
                elif move == 'give':
                    message = giveitem(item, recipient)
                elif move == 'inventory':
                    message = invbuilder(inventory, screen_name)
                else:
                    # if there is a response...
                    if (response != None) and (response[0] != None):
                        # if there is an item...
                        if (newitem != None) and (newitem[0] != None):
                            message = getitem(newitem[0], response[0])
                        # if there isn't an item...
                        else:
                            message = '@' + screen_name + ' ' + response[0] + ' ' + randstring
                    # if there is no valid response
                    else:
                        message = '@' + screen_name + ' Oops, didn\'t work. ' + randstring
                # print reply and tweet it
                print "reply: " + message
                if debug == False:
                    twitter.reply(message, tweetid)
        except:
            pass
cur.close()
conn.close()
