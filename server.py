import os
import json
import requests
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv
from models import init_db, save_recent, get_recents, add_favourite, remove_favourite, get_favourites

# Load environment variables
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # default Groq model

# Initialize the database
init_db()

PROJECT_DIR = os.path.dirname(__file__)
STATIC_DIR = PROJECT_DIR


class SimpleHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # --- API: Get Recents ---
        if path.startswith('/api/recents'):
            recs = get_recents()
            data = [
                {
                    'id': r[0],
                    'company': r[1],
                    'tab': r[2],
                    'prompt': r[3],
                    'response': r[4],
                    'created_at': r[5]
                } for r in recs
            ]
            self._set_headers(200, 'application/json')
            self.wfile.write(json.dumps({'recents': data}).encode('utf-8'))
            return

        # --- API: Get Favourites ---
        if path == '/api/favourites':
            favs = get_favourites()
            data = [
                {'company_id': f[0], 'company_name': f[1], 'created_at': f[2]}
                for f in favs
            ]
            self._set_headers(200, 'application/json')
            self.wfile.write(json.dumps({'favourites': data}).encode('utf-8'))
            return

        # --- Serve Static Files ---
        if path == '/' or path == '/index.html':
            path = '/research.html'

        file_path = os.path.join(STATIC_DIR, path.lstrip('/'))
        if os.path.isfile(file_path):
            ctype = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            self._set_headers(200, ctype)
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f'File Not Found: {self.path}')



    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # --- API: Research Query ---
        if path == '/api/research':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                company = data.get('company', '').strip()
                tab = data.get('tab', '').strip()
                question = data.get('question', '').strip()

                if not company or not question:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'company and question required'}).encode('utf-8'))
                    return

                prompt = f"You are a financial assistant. Provide concise, factual information about {company} focusing on {tab}. Question: {question}"

                # --- Call Groq API ---
                if GROQ_KEY:
                    try:
                        headers = {
                            "Authorization": f"Bearer {GROQ_KEY}",
                            "Content-Type": "application/json",
                        }

                        payload = {
                            "model": GROQ_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a financial assistant for Stock In."},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 800,
                            "temperature": 0.3
                        }

                        r = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=40
                        )

                        print("Groq status:", r.status_code)
                        print("Groq response:", r.text[:400])  # debug log

                        if r.status_code == 200:
                            j = r.json()
                            answer = (
                                j.get("choices", [{}])[0]
                                .get("message", {})
                                .get("content", "[No content returned]")
                            )
                        else:
                            answer = f"[Groq API error {r.status_code}] {r.text}"

                    except Exception as e:
                        answer = f"[Groq API call failed: {str(e)}]"
                else:
                    answer = "[No GROQ_API_KEY set in .env]"

                # Save to recents
                save_recent(company, tab, question, answer)
                self._set_headers(200, 'application/json')
                self.wfile.write(json.dumps({'answer': answer}).encode('utf-8'))

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        
        # add to favourites
        if path == '/api/favourites':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            company_id = data.get('company_id')
            company_name = data.get('company_name')
            is_fav = data.get('isFavourite', True)

            if company_name is None or company_name.strip() == '':
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'company_id and company_name required'}).encode('utf-8'))
                return

            if is_fav:
                add_favourite(company_id, company_name)
            else:
                remove_favourite(company_id)

            self._set_headers(200)
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
            return

        # --- Unknown Endpoint ---
        self._set_headers(404)
        self.wfile.write(json.dumps({'error': 'unknown endpoint'}).encode('utf-8'))

            
    


def run(server_class=HTTPServer, handler_class=SimpleHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving on http://localhost:{port} ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server")
        httpd.server_close()


if __name__ == '__main__':
    run()
