import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tracker.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tracker_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            disease TEXT,
            score REAL,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

# Initialize on module load
init_db()

def save_score(patient_id, disease, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tracker_history (patient_id, disease, score, timestamp) VALUES (?, ?, ?, ?)",
              (patient_id, disease, score, datetime.now()))
    conn.commit()
    conn.close()

def get_history(patient_id, disease):
    """Returns list of (timestamp, score) tuples sorted by time."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, score FROM tracker_history WHERE patient_id=? AND disease=? ORDER BY timestamp ASC",
              (patient_id, disease))
    rows = c.fetchall()
    conn.close()
    
    # Parse datetime strings back to objects if sqlite returns strings
    # SQLite usually returns strings for DATETIME
    data = []
    for ts, sc in rows:
        if isinstance(ts, str):
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
            except:
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                except:
                    dt = datetime.now() # Fallback
        else:
            dt = ts
        data.append((dt, sc))
    return data

def get_last_score(patient_id, disease):
    history = get_history(patient_id, disease)
    if len(history) > 1:
        # Return the score of the *previous* entry (2nd to last)
        # Because the 'current' one might have just been saved or is being computed?
        # The logic in app.py was: compute cur, get previous, THEN save cur.
        # So 'get_last_score' usually meant "most recent saved before this new one".
        # But if we use 'save_score' AFTER logic, then get_last_score should just return the last DB entry.
        # Let's align with app.py usage.
        return history[-1][1]
    elif len(history) == 1:
        return history[0][1]
    return None
