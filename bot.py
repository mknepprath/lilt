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

    for status in tweepy.Cursor(twitter.api.user_timeline).items():
        try:
            twitter.api.destroy_status(status.id)
        except:
            pass

    #mentions = self.api.mentions_timeline(count=1)
    #for mention in mentions:
    #    print mention.text
    #    print mention.user.screen_name

    while True:
        #Send a tweet here!
        time.sleep(60)
        twitter.tweet(message)
