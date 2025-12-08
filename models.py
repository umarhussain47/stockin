import sqlite3
import os
from datetime import datetime
from supabase import create_client, Client

DB_PATH = os.path.join(os.path.dirname(__file__), 'stock_in.db')

# --- Supabase Initialization (for Auth) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Warning: SUPABASE_URL and SUPABASE_ANON_KEY not set.")

supabase: Client = None
try:
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except Exception as e:
    print(f"Supabase client creation failed: {e}")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS recents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL, 
        company TEXT,
        tab TEXT,
        prompt TEXT,
        response TEXT,
        created_at TEXT
    )
    ''')
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS company (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL, 
        company_id INTEGER,
        company_name TEXT,  
        isFavourite INTEGER DEFAULT 0,
        created_at TEXT,
        UNIQUE(user_id, company_name)
    )
    ''')
    
    # Removed initial seeding logic to prevent data without a user_id.

    conn.commit()
    conn.close()

def save_recent(user_id, company, tab, prompt, response):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO recents (user_id, company, tab, prompt, response, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, company, tab, prompt, response, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_recents(user_id, limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, company, tab, prompt, response, created_at
        FROM recents
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (user_id, limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def remove_recent(user_id, rec_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM recents WHERE id = ? AND user_id = ?", (rec_id, user_id))
    conn.commit()
    conn.close()

def add_favourite(user_id, company_id, company_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO company (user_id, company_id, company_name, isFavourite, created_at)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(user_id, company_name) DO UPDATE SET isFavourite = 1
    ''', (user_id, company_id, company_name, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def remove_favourite(user_id, company_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        UPDATE company
        SET isFavourite = 0
        WHERE company_id = ? AND user_id = ?
    ''', (company_id, user_id))
    conn.commit()
    conn.close()


def get_favourites(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT company_id, company_name, created_at
        FROM company
        WHERE isFavourite = 1 AND user_id = ?
        ORDER BY id DESC
    ''', (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows