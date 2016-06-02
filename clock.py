from apscheduler.schedulers.blocking import BlockingScheduler
import logging
logging.basicConfig()

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def timed_job():
    import bot

sched.start()
