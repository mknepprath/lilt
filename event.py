# -*- coding: utf-8 -*-
import db

def getcurrent(move, position, inventory, events):
    events_inv = dict(events)
    items = list(inventory.keys())
    for item in items:
        events_inv[position][item] = 'inventory'
    current_event = None
    for key, value in events_inv[position].iteritems():
        event = {}
        event[key] = value
        # check if there is a response for this move when condition is met (this event)
        response = db.select('response', 'moves', 'move', move, position, event)
        if response != None:
            current_event = event
            break
    return current_event
