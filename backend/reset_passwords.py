import os
import psycopg
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()
_db_url = os.environ.get("DATABASE_URL", "")
DB_URL = _db_url.replace("postgresql+psycopg://", "postgres://").replace("postgresql://", "postgres://")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

new_hash = hash_password("password123")
emails = ["cli-test@example.com", "abhay.verify2@willow.local", "abhaychavda001@willow.local"]

with psycopg.connect(DB_URL) as conn:
    with conn.cursor() as cur:
        for email in emails:
            cur.execute(
                "UPDATE seller_intelligence.users SET hashed_password = %s WHERE email = %s", 
                (new_hash, email)
            )
            print(f"Password reset for: {email}")
        conn.commit()
