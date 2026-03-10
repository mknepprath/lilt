# -*- coding: utf-8 -*-

"""
Mastodon adapter for Lilt. Polls mentions, manages user state, calls engine.
"""

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
import random
import re

import anthropic
from mastodon import Mastodon

import engine

# Persistence paths (use env vars for Railway volume)
_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_USERS_PATH = os.environ.get(
    'USERS_PATH',
    os.path.join(_DATA_DIR, 'data', 'users.json'),
)
_WORLD_PATH = os.environ.get(
    'WORLD_PATH',
    os.path.join(_DATA_DIR, 'data', 'world.json'),
)

MKNEPPRATH = '231610'
DEBUG = bool(os.environ.get('LILT_DEBUG'))

anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)


class HTMLFilter(HTMLParser):
    text = ""

    def handle_data(self, data):
        self.text += data


# --- User state persistence ---

def _load_users():
    if not os.path.exists(_USERS_PATH):
        return []
    with open(_USERS_PATH, 'r') as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []


def _save_users(users):
    os.makedirs(os.path.dirname(_USERS_PATH), exist_ok=True)
    with open(_USERS_PATH, 'w') as f:
        json.dump(users, f, indent=2)


# --- World state persistence ---

def _load_world():
    if not os.path.exists(_WORLD_PATH):
        return {}
    with open(_WORLD_PATH, 'r') as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}


def _save_world(world):
    os.makedirs(os.path.dirname(_WORLD_PATH), exist_ok=True)
    with open(_WORLD_PATH, 'w') as f:
        json.dump(world, f, indent=2)


def _apply_world_update(world, update):
    """Merge a world_update dict into the world state."""
    for position, changes in update.items():
        if position not in world:
            world[position] = {}
        world[position].update(changes)
    return world


def _get_user(user_id):
    for user in _load_users():
        if str(user.get('id')) == str(user_id):
            return user
    return None


def _save_user(user_data):
    users = _load_users()
    for i, user in enumerate(users):
        if str(user.get('id')) == str(user_data['id']):
            users[i] = user_data
            _save_users(users)
            return
    users.append(user_data)
    _save_users(users)


# --- LLM move translation ---

def _get_moves_for_position(position):
    """Return the list of known move strings for a given position."""
    return list({row['move'] for row in engine.MOVES if row.get('position') == position})


def llm_transform(move, position=None):
    valid_moves = _get_moves_for_position(position) if position else []
    if valid_moves:
        moves_hint = "Valid commands for this location: " + ", ".join(
            f"'{m}'" for m in sorted(valid_moves)
        ) + ". "
    else:
        moves_hint = (
            "Example commands: 'inspect X', 'use X on Y', 'open X', 'pick up X', "
            "'go to X', 'eat X', 'drink X', 'talk to X', 'look around', 'look in X', "
            "'look right', 'check inventory', etc. "
        )

    prompt = (
        "You are translating player input for a text adventure game. "
        + moves_hint
        + "Translate the following player input into the closest matching command. "
        "Reply with ONLY the command, nothing else. "
        "Player input: " + move
    )
    try:
        response = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        print("LLM Error:", str(e))
        return None

    text = response.content[0].text
    text = re.split(r'; | // |, |\. |\*|\n', text)[0]
    return engine.normalize(text)


# --- Main bot loop ---

def main():
    mastodon = Mastodon(
        api_base_url=os.environ.get('MASTODON_BASE_URL'),
        client_id=os.environ.get('MASTODON_CLIENT_KEY'),
        client_secret=os.environ.get('MASTODON_CLIENT_SECRET'),
        access_token=os.environ.get('MASTODON_ACCESS_TOKEN'),
    )

    mentions = []
    raw_mentions = mastodon.notifications(limit=100, types=["mention"])

    for mention in raw_mentions:
        skip = False

        if (datetime.now(timezone.utc) - mention.created_at).days > 3:
            skip = True

        if not skip and DEBUG and mention.account.id != int(MKNEPPRATH):
            print("Skipping non-debug mention.")
            skip = True

        if not skip:
            for m in mentions:
                if mention.account.id == m['user_id']:
                    skip = True
                    break

        if not skip:
            f = HTMLFilter()
            f.feed(mention.status.content)
            mentions.append({
                'screen_name': mention.account.acct,
                'user_id': mention.account.id,
                'text': f.text,
                'tweet_id': mention.status.id,
                'visibility': mention.status.visibility,
            })

    world = _load_world()

    for mention in mentions:
        try:
            screen_name = mention['screen_name'].lower()
            user_id = mention['user_id']
            tweet_id = mention['tweet_id']
            visibility = mention['visibility']

            # Extract move text (strip @mention prefix)
            raw_text = mention['text']
            parts = raw_text.split(' ', 1)
            post = parts[1] if len(parts) > 1 else ''
            if post and post[0] == '@':
                post = post.split(' ', 1)[1] if ' ' in post else ''
            post = re.split(r'; | // |, |\. |\*|\n', post)[0]

            # Check if user exists
            user = _get_user(user_id)

            if user is None:
                move = engine.normalize(post)
                if move == 'start':
                    print(f'New player: {screen_name}')
                    result = engine.play('start', world=world)
                    user = {
                        'name': screen_name,
                        'id': user_id,
                        'last_tweet_id': tweet_id,
                        'state': result['state'],
                    }
                    _save_user(user)
                    if result.get('world_update'):
                        world = _apply_world_update(world, result['world_update'])
                        _save_world(world)
                    response_text = result['response']
                else:
                    print(f'{screen_name} is not playing Lilt.')
                    continue
            else:
                # Check if already replied
                if str(user.get('last_tweet_id')) == str(tweet_id):
                    print(f'Already replied to {screen_name}.')
                    continue

                # Migrate old user format if needed
                if 'state' not in user:
                    user['state'] = {
                        'position': user.get('position', 'start'),
                        'inventory': user.get('inventory', {}),
                        'events': user.get('events', {'start': {}}),
                    }

                print(f'Processing move from {screen_name}: {post}')

                # Try the move
                result = engine.play(post, user['state'], world=world)

                # If it was an error, try LLM translation
                if result['response'] in engine.ERROR_MESSAGES:
                    translated = llm_transform(post, user['state'].get('position'))
                    if translated:
                        print(f'LLM translated to: {translated}')
                        result2 = engine.play(translated, user['state'], world=world)
                        if result2['response'] not in engine.ERROR_MESSAGES:
                            result = result2

                response_text = result['response']
                user['state'] = result['state']
                user['last_tweet_id'] = tweet_id
                if not DEBUG:
                    _save_user(user)
                    if result.get('world_update'):
                        world = _apply_world_update(world, result['world_update'])
                        _save_world(world)

            # Send reply — convert literal \n sequences to real newlines
            response_text = response_text.replace('\\n', '\n')
            message = f'@{screen_name} {response_text}'
            print(f'Reply: {message}')
            if not DEBUG:
                mastodon.status_post(
                    status=message,
                    in_reply_to_id=tweet_id,
                    visibility=visibility,
                )

        except Exception as e:
            print(f'Error processing mention: {e}')
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
