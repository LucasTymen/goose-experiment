import psycopg2
import json

conn = psycopg2.connect(
    host="localhost",
    port=5434,
    database="goose_ai",
    user="goose",
    password="goosepass"
)

def insert_audit(action, payload):

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO audit_logs (action, payload)
        VALUES (%s, %s)
        """,
        (action, json.dumps(payload))
    )

    conn.commit()
    cur.close()

