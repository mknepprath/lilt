# -*- coding: utf-8 -*-

"""
Stateless game engine for Lilt.

play(move_text, state) -> {response, state}

State shape:
  {
    "position": "room",
    "inventory": {"coin": {"quantity": 1}},
    "events": {"room": {"chest": "open"}, "start": {}}
  }
"""

import copy
from datetime import datetime
import json
import os
import random
import re
import string


# --- Data loading ---

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

with open(os.path.join(_DATA_DIR, 'moves.json'), 'r') as f:
    MOVES = json.load(f)

with open(os.path.join(_DATA_DIR, 'items.json'), 'r') as f:
    ITEMS = json.load(f)

_ITEMS_BY_NAME = {item['name']: item for item in ITEMS}


# --- Text normalization ---

def normalize(text):
    text = text.strip()
    text = re.sub(r'http\S+', '', text).lower()
    text = re.sub(r' the ', ' ', text)
    text = re.sub(' +', ' ', text)
    text = ''.join(ch for ch in text if ch not in set(string.punctuation)).rstrip()

    if text.startswith('check out'):
        text = 'look at ' + text.split(' ', 2)[2]
    elif text.startswith(('check', 'examine', 'inspect', 'scan', 'see', 'view')):
        text = 'look at ' + text.split(' ', 1)[1]
    elif text.startswith('pick up'):
        text = 'take ' + text.split(' ', 2)[2]
    elif text.startswith(('get', 'grab', 'pick')):
        text = 'take ' + text.split(' ', 1)[1]
    elif text.startswith('shut'):
        text = 'close ' + text.split(' ', 1)[1]

    text = text.replace('liltbluebird', 'bird')
    text = text.replace('blue bird', 'bird')
    text = text.replace('liltmerchant', 'merchant')
    text = text.replace('shopkeeper', 'merchant')
    text = text.replace('apple paste', 'paste')
    text = text.replace(u'\U0001f33a', 'flower')
    text = text.replace('translucent figure', 'spirit')
    text = text.replace('figure', 'spirit')
    text = text.replace('ghost', 'spirit')
    text = text.replace('apparition', 'spirit')
    text = text.replace('phantom', 'spirit')
    text = text.replace(' an ', ' ')
    text = text.replace(' a ', ' ')

    return text


# --- Move lookup ---

def _match_condition(row_cond, query_cond):
    def _norm(c):
        if c is None:
            return None
        if isinstance(c, str):
            try:
                return json.loads(c)
            except (json.JSONDecodeError, ValueError):
                return c
        return c
    return _norm(row_cond) == _norm(query_cond)


def _find_move(move, position, condition=None):
    for row in MOVES:
        if row.get('move') != move or row.get('position') != position:
            continue
        if condition is None:
            if row.get('condition') is not None:
                continue
        else:
            if not _match_condition(row.get('condition'), condition):
                continue
        return row
    return None


def _get_time_period():
    hour = datetime.now().hour
    if 5 <= hour < 8:
        return 'dawn'
    elif 8 <= hour < 18:
        return 'day'
    elif 18 <= hour < 21:
        return 'dusk'
    return 'night'


def _get_current_condition(move, position, inventory, events, world=None):
    state = copy.deepcopy(events)
    if position not in state:
        state[position] = {}
    for item_name in inventory:
        state[position][item_name] = 'inventory'
    # Inject time of day so moves can have time-based conditions
    state[position]['time'] = _get_time_period()
    # Inject world state so moves can check shared state
    if world:
        for key, value in world.get(position, {}).items():
            if key not in state[position]:
                state[position]['world_' + key] = value

    for key, value in state[position].items():
        cond = {key: value}
        result = _find_move(move, position, cond)
        if result is not None:
            return cond
    return None


# --- Inventory helpers ---

def _format_inventory(inventory):
    items = []
    for name, data in inventory.items():
        qty = data.get('quantity', 1)
        if qty > 1:
            items.append(name + ' ' + (u'\u2022' * qty))
        else:
            items.append(name)
    return ', '.join(items)


def _item_get(item_name, inventory, response):
    inv = copy.deepcopy(inventory)
    if item_name not in inv:
        inv[item_name] = {'quantity': 1}
    else:
        item_def = _ITEMS_BY_NAME.get(item_name, {})
        item_max = item_def.get('max', 10)
        if inv[item_name]['quantity'] < item_max:
            inv[item_name]['quantity'] += 1
        else:
            return 'You can\'t hold more {item}!'.format(item=item_name), inventory
    return response, inv


def _item_drop(item_name, inventory, quantity=None):
    inv = copy.deepcopy(inventory)
    if item_name not in inv:
        return 'You don\'t have anything like that.', inventory
    if inv[item_name]['quantity'] <= 1 or quantity == 'all':
        del inv[item_name]
    else:
        inv[item_name]['quantity'] -= 1

    if quantity == 'all':
        return 'You rid yourself of {item}s.'.format(item=item_name), inv
    return 'You drop one {item}.'.format(item=item_name), inv


def _item_replace(old_item, new_item, inventory, response):
    inv = copy.deepcopy(inventory)
    # Add new
    if new_item not in inv:
        inv[new_item] = {'quantity': 1}
    else:
        item_def = _ITEMS_BY_NAME.get(new_item, {})
        item_max = item_def.get('max', 10)
        if inv[new_item]['quantity'] < item_max:
            inv[new_item]['quantity'] += 1
        else:
            return 'You can\'t hold more {item}!'.format(item=new_item), inventory
    # Remove old
    if inv[old_item]['quantity'] <= 1:
        del inv[old_item]
    else:
        inv[old_item]['quantity'] -= 1
    return response, inv


# --- Map ---

_CONNECTIONS = {
    'start': ['room'],
    'room': ['crescent', 'cellar'],
    'cellar': ['tunnels'],
    'tunnels': ['reservoir', 'garden'],
    'reservoir': [],
    'crescent': ['spookytown', 'garden'],
    'garden': [],
    'spookytown': ['graveyard', 'swamp', 'tower'],
    'graveyard': [],
    'swamp': [],
    'tower': ['void'],
    'void': [],
}

_LOCATION_NAMES = {
    'start': 'Start',
    'room': 'Room',
    'cellar': 'Cellar',
    'tunnels': 'Tunnels',
    'reservoir': 'Reservoir',
    'crescent': 'Crescent Plaza',
    'garden': 'Garden',
    'spookytown': 'Spookytown',
    'graveyard': 'Graveyard',
    'swamp': 'Swamp',
    'tower': 'Tower',
    'void': 'Void',
}


def _format_map(position, events):
    visited = set(events.keys())
    lines = []
    for loc_id, name in _LOCATION_NAMES.items():
        if loc_id in visited:
            if loc_id == position:
                lines.append(f'> {name} <')
            else:
                lines.append(f'  {name}')
    unvisited = len(_LOCATION_NAMES) - len(visited & set(_LOCATION_NAMES))
    if unvisited > 0:
        lines.append(f'  ({unvisited} undiscovered)')
    return '\n'.join(lines)


# --- Command handling (drop, inventory, etc.) ---

def _handle_command(words, inventory, position=None, events=None):
    if words[0] == 'drop' and len(words) >= 2:
        quantity = None
        if len(words) >= 3 and words[1] == 'all':
            quantity = 'all'
            item_name = normalize(' '.join(words[2:]))
        elif len(words) >= 3 and words[1] in ('the', 'a', 'an', 'some'):
            item_name = normalize(' '.join(words[2:]))
        else:
            item_name = normalize(' '.join(words[1:]))
        if item_name in _ITEMS_BY_NAME:
            response, new_inv = _item_drop(item_name, inventory, quantity=quantity)
            return response, new_inv
        return None, None

    if words[0] == 'inventory' or ' '.join(words) in (
        'check inventory', 'check my inventory',
        'what am i holding', 'look at inventory'
    ):
        if not inventory:
            return 'Your inventory is empty at the moment.', None
        return _format_inventory(inventory), None

    if words[0] == 'map' or ' '.join(words) in ('show map', 'check map', 'view map'):
        if position is not None and events is not None:
            return _format_map(position, events), None
        return None, None

    return None, None


# --- Main entry point ---

INITIAL_STATE = {
    'position': 'start',
    'inventory': {},
    'events': {'start': {}}
}

ERROR_MESSAGES = [
    'Didn\'t work.',
    'Nice try, but that didn\'t work.',
    'Nice try, but you can\'t do that.',
    'Oops, can\'t do that.',
    'Oops, didn\'t work.',
    'Oops, try something else.',
    'Sorry, you can\'t do that.',
    'Sorry, you\'ll have to try something else.',
    'That can\'t be done.',
    'That didn\'t work.',
    'That doesn\'t seem to do anything.',
    'Try something else.',
    'Try something else, that didn\'t seem to work.',
    'You can\'t do that.',
    'That didn\'t work. Tip: try "look around" to see what\'s nearby.',
    'Hmm, nothing happened. Tip: try "inspect" to examine things more closely.',
    'That didn\'t seem to work. Tip: say "check inventory" to see what you\'re carrying.',
    'Nothing happened. Tip: you can "go to" places you\'ve discovered.',
    'That didn\'t work. Tip: try "pick up" to grab items you find.',
    'Hmm, try something else. Tip: "talk to" characters you meet to learn more.',
    'That can\'t be done. Tip: try "use X on Y" to combine items with things.',
    'Nothing happened. Tip: some things can be opened — try "open" if you see a container.',
]


def play(move_text, state=None, world=None):
    """
    Process a player move and return the result.

    Args:
        move_text: Raw text input from the player.
        state: Current game state dict, or None to start a new game.
        world: Shared world state dict (optional, for multiplayer).

    Returns:
        dict with 'response', 'state', and optionally 'world_update'.
        'world_update' is a dict of {position: {key: value}} to merge
        into the shared world state.
    """
    if state is None:
        state = copy.deepcopy(INITIAL_STATE)

    state = copy.deepcopy(state)
    world = copy.deepcopy(world) if world else {}
    position = state['position']
    inventory = state['inventory']
    events = state['events']

    # Normalize input
    if move_text:
        # Strip semicolons, comments, etc.
        move_text = re.split(r'; | // |, |\. |\*|\n', move_text)[0]
    move = normalize(move_text) if move_text else ''

    # Handle "start" for new game
    if move == 'start' and position == 'start':
        pass  # Fall through to normal move lookup

    # Check commands (drop, inventory)
    words = re.sub(r'http\S+', '', move).lower().split() if move else []
    if words:
        cmd_response, cmd_inventory = _handle_command(words, inventory, position, events)
        if cmd_response is not None:
            if cmd_inventory is not None:
                state['inventory'] = cmd_inventory
            return {'response': cmd_response, 'state': state}

    # Look up move in game data
    condition = _get_current_condition(move, position, inventory, events, world)
    row = _find_move(move, position, condition)

    if row is None:
        return {
            'response': random.choice(ERROR_MESSAGES),
            'state': state
        }

    response = row.get('response')
    item_to_get = row.get('item')
    item_to_drop = row.get('drop')
    trigger = row.get('trigger')
    travel = row.get('travel')
    world_trigger = row.get('world_trigger')

    # Apply trigger (player state change)
    if trigger is not None:
        if isinstance(trigger, str):
            trigger = json.loads(trigger)
        if position not in events:
            events[position] = {}
        events[position].update(trigger)

    # Apply world trigger (shared state change)
    world_update = None
    if world_trigger is not None:
        if isinstance(world_trigger, str):
            world_trigger = json.loads(world_trigger)
        world_update = {position: world_trigger}

    # Apply travel
    if travel is not None:
        position = travel
        state['position'] = position
        if position not in events:
            events[position] = {}

    # Apply inventory changes
    if item_to_get is not None and item_to_drop is not None:
        # Replace item
        response, inventory = _item_replace(item_to_drop, item_to_get, inventory, response)
    elif item_to_get is not None:
        response, inventory = _item_get(item_to_get, inventory, response)
    elif item_to_drop is not None:
        # Drop triggered by game event (not player command)
        _, inventory = _item_drop(item_to_drop, inventory)

    state['inventory'] = inventory
    state['events'] = events

    result = {'response': response, 'state': state}
    if world_update:
        result['world_update'] = world_update
    return result
