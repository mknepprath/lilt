# -*- coding: utf-8 -*-
import db

def getcurrent(move, position, inventory, events):
    ev_inv = events.copy()
    items = list(inventory.keys())
    print events
    for item in items:
        ev_inv[position][item] = 'inventory'
    print events
    current_event = None
    for key, value in ev_inv[position].iteritems():
        e = {}
        e[key] = value
        # check if there is a response for this move when condition is met (this event)
        response = db.select('response', 'moves', 'move', move, position, e)
        if response != None:
            current_event = e
            break
    return current_event
