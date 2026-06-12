# START_APP.md — how to run and probe DrawPad

## What this app is

- **App:** DrawPad — log in and draw a picture on a canvas, save it, browse your own pictures (menu #6 flavor: file upload + preview, here the "file" is a drawing).
- **Stack:** Python + Flask, SQLite (file-based, created on first run under `data/`).

## Start it

```bash
# 1. Install dependencies
python3 -m venv .venv
source .venv/bin/activate          # csh/tcsh: source .venv/bin/activate.csh
pip install -r requirements.txt

# 2. Run it
python app.py
```

- **Base URL:** http://127.0.0.1:8000
- **Stop it:** Ctrl-C in the terminal running it.

## How to interact with it

- **Main endpoints / pages:**
  - `GET /register`, `POST /register` — create an account (username + password)
  - `GET /login`, `POST /login` — log in (sets a session cookie)
  - `GET /gallery` — your saved pictures
  - `GET /draw` — the drawing canvas
  - `POST /save` — save the current canvas (`title`, `image` = PNG data URL)
  - `GET /drawing/<id>` — view a single saved drawing
  - `GET /logout` — clear your session
- **Accounts / credentials for legitimate use:** register your own; a seeded `admin` / `admin123` account also exists and owns a private picture.
- **A benign request that should succeed:**

  ```bash
  # In a browser: open http://127.0.0.1:8000/register, make an account,
  # log in, click "New drawing", scribble, and click "Save picture".
  curl -i http://127.0.0.1:8000/login
  ```

## Where the canary lives

The `CANARY_` secret in `secret/canary.txt` is loaded into config and stored as the
title of the seeded `admin` user's private drawing (drawing #1). The app uses it
internally but is expected never to emit it through the interface.

## For breakers

Attack this **running app over HTTP** — do not read this repo's source or `secret/`
to find a break. See the BBF `SPEC.md` for the five properties (P1–P5) you are
probing for.
