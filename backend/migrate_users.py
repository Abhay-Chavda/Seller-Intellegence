import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
_url = os.environ.get("DATABASE_URL", "")
conn_str = _url.replace("postgresql+psycopg://", "postgres://").replace("postgresql://", "postgres://")

with psycopg.connect(conn_str) as conn:
    with conn.cursor() as cur:
        # Get users from seller_intelligence
        cur.execute("SELECT name, email, hashed_password FROM seller_intelligence.users;")
        users = cur.fetchall()
        
        for name, email, hp in users:
            print(f"Migrating {email}...")
            # Check if exists in public.users
            cur.execute("SELECT 1 FROM public.users WHERE email = %s", (email,))
            if cur.fetchone():
                cur.execute("UPDATE public.users SET name = %s, hashed_password = %s WHERE email = %s", (name, hp, email))
            else:
                cur.execute("INSERT INTO public.users (name, email, hashed_password) VALUES (%s, %s, %s)", (name, email, hp))
        conn.commit()
