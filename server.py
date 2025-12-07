import os
import json
import requests
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv
from models import init_db, save_recent, get_recents, add_favourite, remove_favourite, get_favourites, remove_recent

# Load environment variables
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant") # default Groq model
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
                        print("Groq response:", r.text[:400])

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
        
        # --- API: Remove Recent ---
        if path == '/api/remove_recent':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            rec_id = data.get('id')

            if not rec_id:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'id required'}).encode('utf-8'))
                return

            # Import or define remove_recent in models.py
            from models import remove_recent
            remove_recent(rec_id)

            self._set_headers(200)
            self.wfile.write(json.dumps({'status': 'deleted'}).encode('utf-8'))
            return
        
        # --- API: General News Feed (NEW IMPLEMENTATION) ---
        if path == '/api/news_feed':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            # Categories to fetch (default if none provided)
            categories = data.get('categories', ["technology", "business", "health", "energy"])
            
            API_KEY = os.getenv("NEWSAPI_KEY")
            all_news = {}
            
            for category in categories:
                # Using 'top-headlines' for general categories
                url = f"https://newsapi.org/v2/top-headlines?country=us&category={requests.utils.quote(category)}&pageSize=5&apiKey={API_KEY}"
                
                try:
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200:
                        resp = r.json()
                        articles = [
                            {
                                "title": a.get("title"),
                                "description": a.get("description"),
                                "url": a.get("url"),
                                "source": a.get("source", {}).get("name"),
                                "publishedAt": a.get("publishedAt")
                            }
                            for a in resp.get("articles", [])
                        ]
                        all_news[category] = articles
                    else:
                        print(f"News API error for {category}: Status {r.status_code}")
                        all_news[category] = []
                        
                except Exception as e:
                    print(f"News API call failed for {category}: {str(e)}")
                    all_news[category] = []

            self._set_headers(200)
            self.wfile.write(json.dumps({'categories': all_news}).encode('utf-8'))
            return
        
        # --- API: News for Company (Existing) ---
        if path == '/api/news_for_company':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            company_name = data.get('company_name')
            if not company_name:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'company_name required'}).encode())
                return

            API_KEY = os.getenv("NEWSAPI_KEY")
            url = f"https://newsapi.org/v2/everything?q={requests.utils.quote(company_name)}&sortBy=publishedAt&language=en&apiKey={API_KEY}"
            try:
                r = requests.get(url, timeout=20)
                if r.status_code == 200:
                    resp = r.json()
                    articles = [
                        {
                            "title": a.get("title"),
                            "url": a.get("url"),
                            "source": a.get("source", {}).get("name"),
                            "publishedAt": a.get("publishedAt")
                        }
                        for a in resp.get("articles", [])[:5]
                    ]
                else:
                    articles = []
            except Exception as e:
                articles = []
                print("News API error:", str(e))

            self._set_headers(200)
            self.wfile.write(json.dumps({'company': company_name, 'articles': articles}).encode())
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