import sys
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
_db_url = os.environ.get("DATABASE_URL", "")
DB_URL = _db_url.replace("postgresql+psycopg://", "postgres://").replace("postgresql://", "postgres://")
print(f"Connecting to: {DB_URL.replace('npg_eE0D2zgBqoIb', '***')}")

try:
    conn = psycopg.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name, table_schema 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema');
    """)
    rows = cursor.fetchall()
    print("Tables:")
    for row in rows:
        print(row)
except Exception as e:
    print("Error:", e)
    sys.exit(1)
