import os
import json
import requests
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse
from dotenv import load_dotenv
load_dotenv()

# Import all model functions AND the initialized Supabase client
from models import (
    init_db, save_recent, get_recents, add_favourite, 
    remove_favourite, get_favourites, remove_recent, supabase
)

# Load environment variables

GROQ_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Initialize the database (SQLite data structure & initial seeds)
init_db()

PROJECT_DIR = os.path.dirname(__file__)
STATIC_DIR = PROJECT_DIR


class SimpleHandler(BaseHTTPRequestHandler):
    
    # --- JWT Validation Helper ---
    def _get_user_id_from_auth(self):
        """Extracts and validates the JWT from the Authorization header."""
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        if supabase is None:
            return None
            
        try:
            # Uses Supabase's built-in token verification logic
            res = supabase.auth.get_user(token)
            return res.user.id
        except Exception as e:
            print(f"Token validation failed: {e}")
            return None

    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        
        # --- Auth Check for Protected GET Routes ---
        user_id = None
        if path in ['/api/recents', '/api/favourites']:
            user_id = self._get_user_id_from_auth()
            if user_id is None:
                self._set_headers(401, 'application/json')
                self.wfile.write(json.dumps({'error': 'Unauthorized: Missing or invalid JWT'}).encode('utf-8'))
                return

        # --- API: Get Recents (Protected) ---
        if path.startswith('/api/recents'):
            recs = get_recents(user_id) 
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

        # --- API: Get Favourites (Protected) ---
        if path == '/api/favourites':
            favs = get_favourites(user_id) 
            data = [
                {'company_id': f[0], 'company_name': f[1], 'created_at': f[2]}
                for f in favs
            ]
            self._set_headers(200, 'application/json')
            self.wfile.write(json.dumps({'favourites': data}).encode('utf-8'))
            return
        
        # --- Serve Static Files (Unprotected) ---
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
        
        # Check if Supabase client is available for Auth endpoints
        if supabase is None and path in ['/api/signup', '/api/login']:
            self._set_headers(503)
            self.wfile.write(json.dumps({'error': 'Supabase client not initialized. Check .env keys.'}).encode('utf-8'))
            return
            
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        # --- API: User Signup via Supabase (Unprotected) ---
        if path == '/api/signup':
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Email and password required'}).encode('utf-8'))
                return

            try:
                user_res = supabase.auth.sign_up({"email": email, "password": password})
                
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    'message': 'Signup successful. Check your email for confirmation.', 
                    'user_id': user_res.user.id 
                }).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': f"Signup failed: {str(e)}"}).encode('utf-8'))
            return

        # --- API: User Login via Supabase (Unprotected) ---
        if path == '/api/login':
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Email and password required'}).encode('utf-8'))
                return

            try:
                user_res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                
                access_token = user_res.session.access_token
                user_id = user_res.user.id

                self._set_headers(200)
                self.wfile.write(json.dumps({
                    'message': 'Login successful', 
                    'access_token': access_token, 
                    'user_id': user_id
                }).encode('utf-8'))

            except Exception as e:
                self._set_headers(401)
                self.wfile.write(json.dumps({'error': 'Invalid credentials or login failed'}).encode('utf-8'))
            return

        # --- Auth Check for Protected POST Routes ---
        user_id = self._get_user_id_from_auth()
        if user_id is None and path not in ['/api/news_feed', '/api/news_for_company']:
            self._set_headers(401)
            self.wfile.write(json.dumps({'error': 'Unauthorized: Missing or invalid JWT'}).encode('utf-8'))
            return

        # --- API: Research Query (Protected) ---
        if path == '/api/research':
            
            try:
                company = data.get('company', '').strip()
                tab = data.get('tab', '').strip()
                question = data.get('question', '').strip()

                if not company or not question:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'company and question required'}).encode('utf-8'))
                    return

                prompt = f"You are a financial assistant. Provide concise, factual information about {company} focusing on {tab}. Question: {question}"

                # --- Call Groq API (Unchanged) ---
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
                        
                        if r.status_code == 200:
                            j = r.json()
                            answer = j.get("choices", [{}])[0].get("message", {}).get("content", "[No content returned]")
                        else:
                            answer = f"[Groq API error {r.status_code}] {r.text}"

                    except Exception as e:
                        answer = f"[Groq API call failed: {str(e)}]"
                else:
                    answer = "[No GROQ_API_KEY set in .env]"

                # Save to recents (Now Protected by user_id)
                save_recent(user_id, company, tab, question, answer) 
                self._set_headers(200, 'application/json')
                self.wfile.write(json.dumps({'answer': answer}).encode('utf-8'))

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        
        # add to favourites (Protected)
        if path == '/api/favourites':
            
            company_id = data.get('company_id')
            company_name = data.get('company_name')
            is_fav = data.get('isFavourite', True)

            if company_name is None or company_name.strip() == '':
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'company_id and company_name required'}).encode('utf-8'))
                return

            if is_fav:
                add_favourite(user_id, company_id, company_name) 
            else:
                remove_favourite(user_id, company_id) 

            self._set_headers(200)
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
            return
        
        # --- API: Remove Recent (Protected) ---
        if path == '/api/remove_recent':
            
            rec_id = data.get('id')

            if not rec_id:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'id required'}).encode('utf-8'))
                return

            remove_recent(user_id, rec_id) 
            self._set_headers(200)
            self.wfile.write(json.dumps({'status': 'deleted'}).encode('utf-8'))
            return
        
        # --- API: General News Feed (Unprotected) ---
        if path == '/api/news_feed':
            
            categories = data.get('categories', ["technology", "business", "health", "energy"])
            
            API_KEY = os.getenv("NEWSAPI_KEY")
            all_news = {}
            
            for category in categories:
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
        
        # --- API: News for Company (Unprotected) ---
        if path == '/api/news_for_company':
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