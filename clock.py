"""
Runs bot.py on an interval.
"""

# External
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
import os  # Required despite not being in this file.
import tweepy  # Required despite not being in this file.

logging.basicConfig()

sched = BlockingScheduler()
print('Scheduler created.')


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    filename = 'bot.py'
    print('Run ' + filename + '.')
    exec(compile(open(filename, "rb").read(), filename, 'exec'))


sched.start()
