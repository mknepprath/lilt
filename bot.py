import os
import time
import string
import random
import tweepy
import psycopg2
import urlparse

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

if __name__ == "__main__":
    twitter = TwitterAPI()

    # deletes all tweets so far
    #for status in tweepy.Cursor(twitter.api.user_timeline).items():
    #    try:
    #        print status.text
    #        twitter.api.destroy_status(status.id)
    #    except:
    #        pass

    # init mentions
    mentions = []

    # go through mentions from Twitter using Tweepy
    for mention in tweepy.Cursor(twitter.api.mentions_timeline).items():
        try:
            # splits tweet at first space, game_name = @familiarlilt
            game_name, tweet = (mention.text).split(" ",1)

            # init mentioned
            mentioned = False
            # runs through mentions and notes if current user has been mentioned
            for m in mentions:
                try:
                    if mention.user.id == m['user_id']:
                        mentioned = True
                except:
                    pass

            # if user was already added, don't append it to mentions again
            if mentioned != True:
                mentions.append({
                    'screen_name': mention.user.screen_name,
                    'user_id': mention.user.id,
                    'tweet': tweet,
                    'tweetid': mention.id
                })

        except:
            pass

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

            # might want to add double check to make sure tweet sent
            # if this mention should be replied to, do so
            if reply == True:
                print "tweet: " + tweet

                # removes punctuation and makes move lowercase
                exclude = set(string.punctuation)
                move = ''.join(ch for ch in tweet if ch not in exclude).lower()
                print "move: " + move

                # get position
                cur.execute("SELECT position FROM users WHERE id = %s;", (str(user_id),))
                user = cur.fetchone()
                position = user[0]
                print "position: " + position

                inventory = {}
                inventory['banana'] = {}
                inventory['banana']['quantity'] = 1
                inventory['banana']['health'] = 3
                inventory['rock'] = {}
                inventory['rock']['quantity'] = 1
                inventory['rock']['damage'] = 1

                print inventory['banana']['quantity']
                cur.execute("""UPDATE users SET inventory = %s WHERE id = %s;""", (inventory, str(user_id)))

                # randstring to avoid Twitter getting mad about duplicate tweets
                randstring = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

                # if move is start, init game - otherwise give error
                if (move == "start") and (position == "start"):
                    message = '@' + screen_name + ' You wake up in an unfamiliar room. ' + randstring
                    print "reply: " + message
                    twitter.reply(message, tweetid)
                    cur.execute("UPDATE users SET position = 'room' WHERE id = %s;", (str(user_id),))
                    conn.commit()
                elif (move == "look around") and (position == "room"):
                    message = '@' + screen_name + ' It\'s pretty neat in here. ' + randstring
                    print "reply: " + message
                    twitter.reply(message, tweetid)
                else:
                    message = '@' + screen_name + ' Oops, didn\'t work. ' + randstring
                    print "reply: " + message
                    twitter.reply(message, tweetid)
        except:
            pass

cur.close()
conn.close()
