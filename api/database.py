import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "predictions.db"

def init_db():
    with sqlite3.connect(str(DB_PATH)) as conn:
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

def save_prediction(text: str, label: str, confidence: float, risk_score: int):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO history (timestamp, text, label, confidence, risk_score)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, text, label, confidence, risk_score))
        conn.commit()

def get_history(limit=6):
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, text, label, confidence, risk_score 
            FROM history 
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
    
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

def get_stats() -> dict:
    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM history")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM history WHERE risk_score >= 70")
        high_risk = cursor.fetchone()[0]
    return {"docs_analyzed": total, "high_risk_flags": high_risk}
