# -*- coding: utf-8 -*-

"""
HTTP API for Lilt game engine.

POST /move  {move: "look around", state: {...}}
  -> {response: "...", state: {...}}

POST /start
  -> {response: "...", state: {...}}
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

import engine

app = Flask(__name__)
CORS(app)


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
    return jsonify(result)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
