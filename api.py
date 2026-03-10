# -*- coding: utf-8 -*-

"""
HTTP API for Lilt game engine.

POST /move  {move: "look around", state: {...}}
  -> {response: "...", state: {...}}

POST /start
  -> {response: "...", state: {...}}
"""

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

_anthropic_client = None


def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def llm_transform(move):
    client = _get_client()
    if not client:
        return None

    prompt = (
        "Example commands: 'inspect X', 'use X on Y', 'open X', 'pick up X', "
        "'go to X', 'eat X', 'drink X', 'talk to X', 'look around', 'look in X', "
        "'look right', 'check inventory', etc. to play the game. "
        "Translate the following into a command: " + move + ". Command:"
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
    result = engine.play('start')
    return jsonify(result)


@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    if not data or 'move' not in data or 'state' not in data:
        return jsonify({'error': 'Request must include "move" and "state".'}), 400

    result = engine.play(data['move'], data['state'])

    # If the engine didn't recognize the move, try LLM translation
    if result['response'] in engine.ERROR_MESSAGES:
        translated = llm_transform(data['move'])
        if translated:
            result2 = engine.play(translated, data['state'])
            if result2['response'] not in engine.ERROR_MESSAGES:
                result = result2

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
    while True:
        time.sleep(_POLL_INTERVAL)
        try:
            import mastodon_bot
            mastodon_bot.main()
            print(f'[LILT] Poll complete')
        except Exception as e:
            print(f'[LILT] Poll error: {e}')
            import traceback
            traceback.print_exc()


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
