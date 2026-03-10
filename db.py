# -*- coding: utf-8 -*-

import json
import os

# Internal
from constants import COLOR, DEBUG

# Paths to JSON data files (relative to this file's directory)
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
_MOVES_PATH = os.path.join(_DATA_DIR, 'moves.json')
_ITEMS_PATH = os.path.join(_DATA_DIR, 'items.json')
# On AWS Lambda, use S3 for persistent user state (Lambda filesystem is ephemeral).
# Locally, store alongside the other data files.
_ON_LAMBDA = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
_S3_BUCKET = 'liltbot'
_S3_USERS_KEY = 'users.json'
_USERS_PATH = os.path.join(_DATA_DIR, 'users.json')

# Load read-only game data
with open(_MOVES_PATH, 'r') as f:
    _moves = json.load(f)

with open(_ITEMS_PATH, 'r') as f:
    _items = json.load(f)


def _load_users():
    """Load users from S3 (Lambda) or local JSON file."""
    if _ON_LAMBDA:
        import boto3
        try:
            s3 = boto3.client('s3')
            obj = s3.get_object(Bucket=_S3_BUCKET, Key=_S3_USERS_KEY)
            return json.loads(obj['Body'].read().decode('utf-8'))
        except Exception:
            return []
    if not os.path.exists(_USERS_PATH):
        return []
    with open(_USERS_PATH, 'r') as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []


def _save_users(users):
    """Save users to S3 (Lambda) or local JSON file."""
    if _ON_LAMBDA:
        import boto3
        s3 = boto3.client('s3')
        s3.put_object(Bucket=_S3_BUCKET, Key=_S3_USERS_KEY,
                      Body=json.dumps(users, indent=2).encode('utf-8'),
                      ContentType='application/json')
        return
    with open(_USERS_PATH, 'w') as f:
        json.dump(users, f, indent=2)


def _match_condition(row_condition, query_condition):
    """Check if a row's condition field matches the query condition.

    Both can be None, a dict, or a JSON string representing a dict.
    """
    # Normalize row_condition to a comparable form
    if row_condition is None:
        row_cond = None
    elif isinstance(row_condition, str):
        try:
            row_cond = json.loads(row_condition)
        except (json.JSONDecodeError, ValueError):
            row_cond = row_condition
    else:
        row_cond = row_condition

    # Normalize query_condition
    if query_condition is None:
        query_cond = None
    elif isinstance(query_condition, str):
        try:
            query_cond = json.loads(query_condition)
        except (json.JSONDecodeError, ValueError):
            query_cond = query_condition
    else:
        query_cond = query_condition

    return row_cond == query_cond


def _get_table(table):
    """Return the appropriate data list for a given table name."""
    if table == 'moves':
        return _moves
    elif table == 'items':
        return _items
    elif table == 'users':
        return _load_users()
    else:
        return []


def _get_field(row, col):
    """Get a field value from a row dict.

    For users, inventory and events need special handling:
    - inventory is returned as a dict (parsed from JSON if needed)
    - events is returned as a JSON string (for compatibility with bot.py's json.loads call)
    """
    val = row.get(col)
    return val


def select(col1, table, col2, val, position=None, condition=None, quantity='one'):
    data = _get_table(table)

    # Filter rows where col2 == val
    # Values are compared as strings since the original SQL used string comparison
    matching = []
    for row in data:
        row_val = row.get(col2)
        if row_val is None:
            continue
        # Compare as strings to match original SQL behavior
        if str(row_val) == str(val):
            matching.append(row)

    if position is not None:
        # Further filter by position and condition
        filtered = []
        for row in matching:
            if str(row.get('position', '')) != str(position):
                continue
            # Match condition: if condition is None, row's condition must be None
            # If condition is provided, row's condition must match
            if condition is None:
                if row.get('condition') is not None:
                    continue
            else:
                if not _match_condition(row.get('condition'), condition):
                    continue
            filtered.append(row)
        matching = filtered

    if quantity == 'one':
        if not matching:
            if DEBUG.DB:
                print(COLOR.BLUE + 'Returning None.' + COLOR.END)
            return None
        result = matching[0].get(col1)
        if DEBUG.DB:
            print(COLOR.BLUE + 'Returning one.' + COLOR.END)
        # For user fields stored as JSON strings in the original DB:
        # inventory needs to be a dict, events needs to be a JSON string.
        # In our JSON file, both are stored as native dicts/objects.
        if table == 'users' and col1 == 'inventory':
            if isinstance(result, str):
                result = json.loads(result)
        elif table == 'users' and col1 == 'events':
            if isinstance(result, dict):
                result = json.dumps(result)
        return result
    else:
        if DEBUG.DB:
            print(COLOR.BLUE + 'Returning all:' + COLOR.END,
                  [(row.get(col1),) for row in matching])
        # Return as list of tuples to match psycopg2's fetchall() format
        return [(row.get(col1),) for row in matching]


def update_user(val1, user_id, col='inventory'):
    if DEBUG.DB:
        print(COLOR.BLUE + 'Updating database.' + COLOR.END)

    users = _load_users()
    for user in users:
        if str(user.get('id')) == str(user_id):
            # Store the value natively (as dict if it's a dict, string otherwise)
            user[col] = val1
            break
    _save_users(users)


def delete(table, column, value):
    if table == 'users':
        users = _load_users()
        users = [u for u in users if str(u.get(column)) != str(value)]
        _save_users(users)
    elif table == 'moves':
        global _moves
        _moves = [m for m in _moves if str(m.get(column)) != str(value)]
        _save_moves()
    elif table == 'items':
        global _items
        _items = [i for i in _items if str(i.get(column)) != str(value)]
        _save_items()


def create_new_user(name, user_id, tweet_id):
    print(COLOR.BLUE + 'Creating new user.' + COLOR.END)
    users = _load_users()
    users.append({
        'name': name,
        'id': user_id,
        'last_tweet_id': tweet_id,
        'position': 'start',
        'inventory': {},
        'events': {'start': {}}
    })
    _save_users(users)


# --- Admin functions ---

def _save_moves():
    """Save moves back to JSON (for admin modifications)."""
    with open(_MOVES_PATH, 'w') as f:
        json.dump(_moves, f, indent=2)


def _save_items():
    """Save items back to JSON (for admin modifications)."""
    with open(_ITEMS_PATH, 'w') as f:
        json.dump(_items, f, indent=2)


def new_move(move, response, position, traits=None):
    global _moves
    entry = {'move': move, 'response': response, 'position': position,
             'item': None, 'condition': None, 'trigger': None,
             'drop': None, 'travel': None}
    if traits is not None:
        entry.update(traits)
    _moves.append(entry)
    _save_moves()


def copy_move(ogmove, new_move_name, position):
    global _moves
    for row in _moves:
        if row.get('move') == ogmove and row.get('position') == position:
            new_entry = dict(row)
            new_entry['move'] = new_move_name
            _moves.append(new_entry)
            _save_moves()
            return


def new_item(traits):
    global _items
    entry = {'name': None, 'health': None, 'damage': None,
             'max': None, 'give': None}
    entry.update(traits)
    _items.append(entry)
    _save_items()


def do(action, table, data, val=None):
    if action == 'insert':
        table_data = _get_table(table)
        if table == 'moves':
            global _moves
            entry = {'move': None, 'response': None, 'position': None,
                     'item': None, 'condition': None, 'trigger': None,
                     'drop': None, 'travel': None}
            entry.update(data)
            _moves.append(entry)
            _save_moves()
        elif table == 'items':
            global _items
            entry = {'name': None, 'health': None, 'damage': None,
                     'max': None, 'give': None}
            entry.update(data)
            _items.append(entry)
            _save_items()
        elif table == 'users':
            users = _load_users()
            users.append(data)
            _save_users(users)

    elif action == 'select':
        table_data = _get_table(table)
        results = []
        for row in table_data:
            match = True
            for key, value in data.items():
                row_val = row.get(key)
                # Handle dict comparisons (condition/trigger fields)
                if isinstance(value, dict):
                    if not _match_condition(row_val, value):
                        match = False
                        break
                elif str(row_val) != str(value) if row_val is not None else True:
                    match = False
                    break
            if match:
                results.append((row.get(val),))
        return results

    elif action == 'delete':
        if table == 'moves':
            _moves[:] = [row for row in _moves if not _row_matches(row, data)]
            _save_moves()
        elif table == 'items':
            _items[:] = [row for row in _items if not _row_matches(row, data)]
            _save_items()
        elif table == 'users':
            users = _load_users()
            users = [row for row in users if not _row_matches(row, data)]
            _save_users(users)

    elif action == 'update':
        if table == 'moves':
            for row in _moves:
                if _row_matches(row, data):
                    for k, v in val.items():
                        row[k] = v
            _save_moves()
        elif table == 'items':
            for row in _items:
                if _row_matches(row, data):
                    for k, v in val.items():
                        row[k] = v
            _save_items()
        elif table == 'users':
            users = _load_users()
            for row in users:
                if _row_matches(row, data):
                    for k, v in val.items():
                        row[k] = v
            _save_users(users)

    return None


def _row_matches(row, data):
    """Check if a row matches all key-value pairs in data."""
    for key, value in data.items():
        row_val = row.get(key)
        if isinstance(value, dict):
            if not _match_condition(row_val, value):
                return False
        else:
            if row_val is None:
                return False
            if str(row_val) != str(value):
                return False
    return True
