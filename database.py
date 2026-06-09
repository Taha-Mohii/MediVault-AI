import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DB_URL)


def add_patient(name,age,condition,doctor,hospital):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO patients (name,age,condition,doctor,hospital)VALUES (%s, %s, %s, %s,%s)
""", (name,age,condition,doctor,hospital))
    conn.commit()
    conn.close()

def get_all_patients():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_patient(patient_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = %s",(patient_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_patient(patient_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id = %s",(patient_id,))
    conn.commit()
    conn.close()
