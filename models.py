import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'stock_in.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS recents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        tab TEXT,
        prompt TEXT,
        response TEXT,
        created_at TEXT
    )
    ''')
    conn.commit()
    conn.close()

def save_recent(company, tab, prompt, response):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO recents (company, tab, prompt, response, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (company, tab, prompt, response, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_recents(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT id, company, tab, prompt, response, created_at
        FROM recents
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
