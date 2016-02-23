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
        """Send a tweet"""
        self.api.update_status(status=message, in_reply_to_status_id=tweetid)

if __name__ == "__main__":
    twitter = TwitterAPI()

    #for status in tweepy.Cursor(twitter.api.user_timeline).items():
    #    try:
    #        print status.text
    #        twitter.api.destroy_status(status.id)
    #    except:
    #        pass

    for mention in tweepy.Cursor(twitter.api.mentions_timeline).items():
        try:

            screen_name = mention.user.screen_name
            user_id = mention.user.id
            game_name, tweet = (mention.text).split(" ",1)
            tweetid = mention.id

            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            cur.execute("SELECT EXISTS(SELECT 1 FROM users WHERE name=%s) AS 'exists';")
            user_exists = cur.fetchone()
            print "user exists: " + user_exists

            cur.execute("INSERT INTO users (name, id, last_tweet_id) VALUES (%s, %s, %s)", (screen_name, user_id, tweetid))
            #conn.commit()

            print tweet

            randstring = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

            if tweet == "start":
                message = '@' + screen_name + ' You wake up in an unfamiliar room. ' + randstring
                print message
                twitter.reply(message, tweetid)
            else:
                message = '@' + screen_name + ' Oops, didn\'t work. ' + randstring
                print message
                twitter.reply(message, tweetid)
        except:
            pass

cur.close()
conn.close()
