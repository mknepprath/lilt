# -*- coding: utf-8 -*-

"""
HTTP API for Lilt game engine.

POST /move  {move: "look around", state: {...}}
  -> {response: "...", state: {...}}

POST /start
  -> {response: "...", state: {...}}
"""

import json
import os
import re
import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

import anthropic
import engine

app = Flask(__name__)
CORS(app)

# --- World state persistence (shared across all players) ---

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_WORLD_PATH = os.environ.get(
    'WORLD_PATH',
    os.path.join(_DATA_DIR, 'data', 'world.json'),
)
_world_lock = threading.Lock()


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
    for position, changes in update.items():
        if position not in world:
            world[position] = {}
        world[position].update(changes)
    return world

_anthropic_client = None


def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def _get_moves_for_position(position):
    """Return the list of known move strings for a given position."""
    return list({row['move'] for row in engine.MOVES if row.get('position') == position})


def llm_transform(move, position=None):
    client = _get_client()
    if not client:
        return None

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
        response = client.messages.create(
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


@app.route('/start', methods=['POST'])
def start():
    with _world_lock:
        world = _load_world()
        result = engine.play('start', world=world)
        if result.get('world_update'):
            world = _apply_world_update(world, result['world_update'])
            _save_world(world)
    return jsonify(result)


@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    if not data or 'move' not in data or 'state' not in data:
        return jsonify({'error': 'Request must include "move" and "state".'}), 400

    with _world_lock:
        world = _load_world()
        result = engine.play(data['move'], data['state'], world=world)

        # If the engine didn't recognize the move, try LLM translation
        if result['response'] in engine.ERROR_MESSAGES:
            translated = llm_transform(data['move'], data['state'].get('position'))
            if translated:
                result2 = engine.play(translated, data['state'], world=world)
                if result2['response'] not in engine.ERROR_MESSAGES:
                    result = result2

        if result.get('world_update'):
            world = _apply_world_update(world, result['world_update'])
            _save_world(world)

    return jsonify(result)


@app.route('/poll', methods=['POST'])
def poll():
    """Trigger Mastodon mention polling. Called by Railway cron."""
    secret = request.headers.get('Authorization', '')
    expected = os.environ.get('POLL_SECRET', '')
    if not expected or secret != f'Bearer {expected}':
        return jsonify({'error': 'unauthorized'}), 401

    try:
        import mastodon_bot
        mastodon_bot.main()
        return jsonify({'status': 'polled'})
    except Exception as e:
        print(f'[LILT] Poll error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


# --- Background Mastodon polling ---

_POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', 300))  # seconds, default 5 min


def _poll_loop():
    """Background thread that polls Mastodon mentions on a timer."""
    failures = 0
    while True:
        time.sleep(_POLL_INTERVAL)
        try:
            import mastodon_bot
            mastodon_bot.main()
            print('[LILT] Poll complete')
            failures = 0
        except Exception as e:
            failures += 1
            print(f'[LILT] Poll error ({failures}): {e}')
            if failures >= 3:
                print('[LILT] Too many failures, stopping poller. Fix credentials and redeploy.')
                return


def _start_poller():
    if not os.environ.get('MASTODON_ACCESS_TOKEN'):
        print('[LILT] No MASTODON_ACCESS_TOKEN set, skipping poller')
        return
    t = threading.Thread(target=_poll_loop, daemon=True)
    t.start()
    print(f'[LILT] Mastodon poller started (every {_POLL_INTERVAL}s)')


_start_poller()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
