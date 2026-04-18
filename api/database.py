import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "predictions.db"

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            text TEXT NOT NULL,
            label TEXT NOT NULL,
            confidence REAL NOT NULL,
            risk_score INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_prediction(text: str, label: str, confidence: float, risk_score: int):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    cursor.execute("""
        INSERT INTO history (timestamp, text, label, confidence, risk_score)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, text, label, confidence, risk_score))
    
    conn.commit()
    conn.close()

def get_history(limit=6):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, text, label, confidence, risk_score 
        FROM history 
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "timestamp": row[0],
            "preview": row[1][:120].strip().replace("\n", " "),
            "label": row[2],
            "confidence": row[3],
            "risk_score": row[4]
        })
    return history
