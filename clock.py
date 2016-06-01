from apscheduler.schedulers.blocking import BlockingScheduler
import logging

logging.basicConfig()
sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=3)
def timed_job():
    execfile('bot.py')

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=17)
def scheduled_job():
    execfile('bot.py')

sched.start()
