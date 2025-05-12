import os
import psycopg2

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
CONNECTION_ID = os.getenv("CONNECTION_ID")
DB_PORT = int(os.getenv("DB_PORT", "6432"))
VERBOSE_LOG = os.getenv("VERBOSE_LOG", "False").lower() == "true"

def connect_to_db(context):
    return psycopg2.connect(
        database=CONNECTION_ID,
        user=DB_USER,
        password=context.token["access_token"],
        host=DB_HOST,
        port=DB_PORT,
        sslmode="require"
    )