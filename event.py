# -*- coding: utf-8 -*-

"""
Functions for checking player state.
"""

# Internal
import copy
import db


def get_current_event(move, position, inventory, state):
    # TODO: `events` should perhaps be renamed "state" - it persists the current
    # state of the player's environment bucketed by location.

    # Creating a copy of events to modify.
    state_and_inventory = copy.deepcopy(state)

    # Getting the list of items in the player's inventory.
    items = list(inventory.keys())

    # Here, I'm doing some weird stuff. On top of existing state, I'm adding
    # inventory.
    for item in items:
        state_and_inventory[position][item] = 'inventory'

    # Here's where checking if any of the state is applicable to the current
    # player move.
    current_event = None
    # Loop through each key/value pair in state (and the inventory)...
    for key, value in state_and_inventory[position].items():
        # Rebuild dict from key/value pair for querying.
        event = {}
        event[key] = value

        # Check if there is a response for this move for any current state.
        response = db.select('response', 'moves', 'move',
                             move, position, event)

        # If we did get a response, there is a stateful response for this move.
        # Store that state and break the loop.
        if response != None:
            current_event = event
            break

    print("Returning current event:", current_event)
    return current_event
