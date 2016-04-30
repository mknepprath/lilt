# -*- coding: utf-8 -*-
import db

def getcurrent(move, position, inventory, events):
    print '5: ' + str(events)
    events_inv = events
    print '7: ' + str(events)
    items = list(inventory.keys())
    print '9: ' + str(events)
    for item in items:
        print '11: ' + str(events)
        events_inv[position][item] = 'inventory'
    print '13: ' + str(events)
    current_event = None
    for key, value in events_inv[position].iteritems():
        event = {}
        event[key] = value
        # check if there is a response for this move when condition is met (this event)
        response = db.select('response', 'moves', 'move', move, position, event)
        if response != None:
            current_event = event
            break
    print '23: ' + str(events)
    return current_event
