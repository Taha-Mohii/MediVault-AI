import psycopg2
import os
import time
from dotenv import load_dotenv
from supabase import create_client
from reportlab.lib.pagesizes import A4 
from reportlab.pdfgen import canvas
import io


load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL,SUPABASE_KEY)

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
    cursor.execute("DELETE FROM vitals WHERE patient_id = %s",(patient_id,))
    cursor.execute("DELETE FROM patients WHERE id = %s",(patient_id,))
    conn.commit()
    conn.close()


# VITALS SECTION..
def add_vitals(patient_id , date ,temperature , bp_systolic , bp_diastolic , sugar , weight ,heart_rate):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO vitals (patient_id , date , temperature , bp_systolic , bp_diastolic,sugar,weight,heart_rate)
                   VALUES(%s, %s, %s,%s ,%s ,%s ,%s ,%s)
                   """,(patient_id,  date ,temperature , bp_systolic , bp_diastolic , sugar , weight ,heart_rate))
    conn.commit()
    conn.close()
def get_vitals(patient_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vitals where patient_id = %s  ORDER BY date DESC",(patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
    

def get_patient_summary(patient_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = %s",(patient_id,))
    patient = cursor.fetchone()

    cursor.execute("SELECT * FROM vitals WHERE patient_id = %s ORDER BY date DESC LIMIT 5", (patient_id,))
    vitals = cursor.fetchall()
    conn.close()

    summary = f"""
Patient Name: {patient[1]}
Age: {patient[2]}
Medical Condition: {patient[3]}
Doctor: {patient[4]}
Hospital: {patient[5]}

Recent Vitals:
"""
    if vitals:
        for v in vitals:
            summary +=  f"\nDate: {v[2]} | Temp: {v[3]}°C | BP: {v[4]}/{v[5]} | Sugar: {v[6]} | Weight: {v[7]}kg | Heart Rate: {v[8]}bpm"
    else:
        summary += "No Vitals Recorded Yet."
    return summary


#REPORTS SECTION
def upload_reports(patient_id,filename,category,file_bytes,content_type):
    unique_filename = f"{int(time.time())}_{filename}"
    path = f"{patient_id}/{unique_filename}"
    supabase.storage.from_("Reports").upload(path,file_bytes,{"content-type": content_type})
    file_url = supabase.storage.from_("Reports").get_public_url(path)
    conn = get_conn()
    cursor =conn.cursor()
    cursor.execute("""
        INSERT INTO reports (patient_id,filename,category,file_url)
        VALUES (%s,%s,%s,%s)
    """,(patient_id,unique_filename,category,file_url))
    conn.commit()
    conn.close()

def get_reports(patient_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE patient_id = %s ORDER BY uploaded_at DESC",(patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_reports(report_id, patient_id, filename):
    path = f"{patient_id}/{filename}"
    supabase.storage.from_("Reports").remove([path])
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE id = %s",(report_id,))
    conn.commit()
    conn.close()
    

#MEDICATION SECTION
def add_medication(patient_id ,name ,dose ,frequency, timing):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medications (patient_id, name, dose, frequency, timing)
        VALUES (%s, %s, %s, %s, %s)
    """, (patient_id, name, dose, frequency, timing))
    conn.commit()
    conn.close()

def get_medications(patient_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medications WHERE patient_id = %s",(patient_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_medication(medication_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medications WHERE id = %s",(medication_id,))
    conn.commit()
    conn.close()

def delete_patient(patient_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vitals where patient_id=%s",(patient_id,))
    cursor.execute("DELETE FROM medications WHERE patient_id = %s", (patient_id,))
    cursor.execute("DELETE FROM reports WHERE patient_id = %s", (patient_id,))
    cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
    conn.commit()
    conn.close()

def delete_vitals(vital_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vitals WHERE id = %s",(vital_id,))
    conn.commit()
    conn.close()

#PDF SUMMARY GEN
def generate_summary_pdf(patient, response):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold",20)
    c.drawString(50,height - 50, "MediVault — Doctor Visit Summary ")

    c.setFont("Helvetica",12)
    c.drawString(50,height - 80, f"Patient: {patient[1]}")
    c.drawString(50, height - 100, f"Age: {patient[2]}   |  Condition: {patient[3]}")
    c.drawString(50, height - 120, f"Doctor: {patient[4]}    |   Hospital: {patient[5]}")

    c.line(50, height - 135, width - 50, height - 135)

    y = height - 160
    c.setFont("Helvetica", 11)
    for line in response.split("\n"):
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)
        c.drawString(50, y, line[:100])
        y -= 18

    c.save()
    buf.seek(0)
    return buf

