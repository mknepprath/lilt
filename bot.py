import os
import time
import string
import random
import tweepy

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

if __name__ == "__main__":
    twitter = TwitterAPI()
    message = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
    print message

    for mention in tweepy.Cursor(twitter.api.mentions_timeline).items():
        try:
            print mention.id
            print mention.user.screen_name
            print mention.text
        except:
            pass

    twitter.tweet(message)
