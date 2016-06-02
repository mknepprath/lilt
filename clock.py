from apscheduler.schedulers.blocking import BlockingScheduler
import logging
import os
import tweepy

logging.basicConfig()

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def timed_job():
    execfile('bot.py')

sched.start()
