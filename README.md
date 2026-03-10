# Lilt

A text adventure game. Play it at [mknepprath.com/lilt](https://mknepprath.com/lilt) or on [Mastodon](https://mastodon.social/@familiarlilt).

## Architecture

- **`engine.py`** — Stateless game engine. `play(move, state) → {response, state}`
- **`api.py`** — Flask API wrapping the engine (deployed on Railway)
- **`mastodon_bot.py`** — Mastodon adapter with user state persistence
- **`cli.py`** — Command-line interface for local play
- **`data/`** — Game data (moves, items) as JSON

## Run locally

```
pip install -r requirements.txt
python cli.py
```

## API

```
POST /start         → {response, state}
POST /move          → {move, state} → {response, state}
GET  /health        → {status}
```

State is passed by the client with each request. The API is stateless.
