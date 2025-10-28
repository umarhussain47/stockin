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
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS company (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        company_name TEXT UNIQUE,
        isFavourite INTEGER DEFAULT 0,
        created_at TEXT
    )
    ''')
    
    # ✅ Seed initial companies if none exist
    cur.execute('SELECT COUNT(*) FROM company')
    count = cur.fetchone()[0]
    if count == 0:
        companies = [
            (1, 'Microsoft'),
            (2, 'Tesla'),
            (3, 'Google'),
            (4, 'Apple'),
            (5, 'Amazon'),
            (6, 'Meta'),
            (7, 'Netflix'),
            (8, 'Nvidia'),
            (9, 'Adobe'),
            (10, 'Intel'),
            (11, 'Salesforce'),
            (12, 'Oracle'),
            (13, 'IBM'),
            (14, 'Spotify')
        ]
        now = datetime.utcnow().isoformat()
        cur.executemany('''
            INSERT INTO company (company_id, company_name, isFavourite, created_at)
            VALUES (?, ?, 0, ?)
        ''', [(cid, cname, now) for cid, cname in companies])
        print(f"✅ Seeded {len(companies)} companies")

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

def remove_recent(rec_id):
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM recents WHERE id = ?", (rec_id,))
    conn.commit()
    conn.close()

def add_favourite(company_id, company_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # insert or update if already exists
    cur.execute('''
        INSERT INTO company (company_id, company_name, isFavourite, created_at)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(company_name) DO UPDATE SET isFavourite = 1
    ''', (company_id, company_name, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()


def remove_favourite(company_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        UPDATE company
        SET isFavourite = 0
        WHERE company_id = ?
    ''', (company_id,))
    conn.commit()
    conn.close()


def get_favourites():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT company_id, company_name, created_at
        FROM company
        WHERE isFavourite = 1
        ORDER BY id DESC
    ''')
    rows = cur.fetchall()
    conn.close()
    return rows
