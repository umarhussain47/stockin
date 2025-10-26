# Stock In (Minimal)
**Authors:** UMAR HUSSAIN, 27132; FARIS IJAZ

## What this delivers
- Python backend (no web framework) using `http.server` + `BaseHTTPRequestHandler`.
- SQLite database to store recent research queries.
- Frontend: HTML/CSS/JS for Research and Recents pages.
- `.env` support for `OPENAI_API_KEY` (uses python-dotenv).
- MVC-like split: `models.py` (DB), `server.py` (controller).
- Simple integration with OpenAI (requires `openai` package and valid key in `.env`).

## Run locally (VSCode)
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Put your OpenAI API key in `.env` (the repo contains an example).
3. Run the server:
   ```
   python server.py
   ```
4. Open browser: http://localhost:8000/research.html and http://localhost:8000/recents.html

## Notes
- Authentication is intentionally NOT implemented per instructions.
- Only Research and Recents pages are implemented.
- The server will store every research request into SQLite and show them on Recents.
