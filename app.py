from flask import Flask , render_template,request,redirect,url_for
from database import add_patient,get_all_patients,get_patient,delete_patient,add_vitals,get_vitals,get_patient_summary,upload_reports,get_reports,delete_reports,add_medication,delete_medication,get_medications,delete_vitals,generate_summary_pdf
from dotenv import load_dotenv
from flask import send_file
load_dotenv()
from groq import Groq
import os

app = Flask(__name__)

@app.route("/")
def index():
    patients  = get_all_patients()
    return render_template("index.html", patients = patients)


@app.route("/add",methods = ["GET" ,"POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        condition = request.form["condition"]
        doctor = request.form["doctor"]
        hospital = request.form["hospital"]
        add_patient(name,age,condition,doctor,hospital)
        return redirect(url_for("index"))
    return render_template("add.html")


@app.route("/patient/<int:patient_id>")
def patient(patient_id):
    p = get_patient(patient_id)
    return render_template("patient.html", patient = p)

@app.route("/delete/<int:patient_id>")
def delete(patient_id):
    delete_patient(patient_id)
    return redirect(url_for("index"))

@app.route("/patient/<int:patient_id>/add_vitals",methods=["GET" , "POST"])
def log_vitals(patient_id):
    if request.method == "POST":
        date = request.form["date"]
        temperature = request.form["temperature"]
        bp_systolic = request.form["bp_systolic"]
        bp_diastolic = request.form["bp_diastolic"]
        sugar = request.form["sugar"]
        weight = request.form["weight"]
        heart_rate = request.form["heart_rate"]
        add_vitals(patient_id,date,temperature,bp_systolic,bp_diastolic,sugar,weight,heart_rate)
        return redirect(url_for("patient",patient_id = patient_id))
    return render_template("add_vitals.html",patient_id = patient_id)
    
@app.route("/patient/<int:patient_id>/vitals")
def view_vitals(patient_id):
    p = get_patient(patient_id)
    vitals = get_vitals(patient_id)
    return render_template("vitals.html",patient=p,vitals=vitals)


client = Groq(api_key = os.getenv("GROQ_API_KEY"))
@app.route("/patient/<int:patient_id>/ai", methods = ["GET" , "POST"])
def ai_assistant(patient_id):
    p = get_patient(patient_id)
    response = None
    if request.method == "POST":
        question = request.form["question"]
        summary = get_patient_summary(patient_id)
        messages = [
            {
                "role" : "system",
                "content" : f""" you are MediVaut Ai namely MedEx a helpful medical assistant.
you have access to the following patient data:
{summary}
Answer questions based on this patient's data. Give dietary suggestions, explain vitals, and provide general health guidance.
Always remind the user to consult their doctor for medical decisions.
keep responses clear and simple."""
            },
            {
                "role" : "user",
                "content": question
            }
        ]
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        response = chat.choices[0].message.content
    return render_template("ai.html",patient = p , response = response)

#REPORTS
@app.route("/patient/<int:patient_id>/upload",methods=["GET" , "POST"])
def upload(patient_id):
    p = get_patient(patient_id)
    if request.method == "POST":
        file = request.files["file"]
        category = request.form["category"]
        file_bytes = file.read()
        content_type = file.content_type
        upload_reports(patient_id,file.filename,category,file_bytes,content_type)
        return redirect(url_for("report", patient_id = patient_id))
    return render_template("upload.html",patient=p)

@app.route("/patient/<int:patient_id>/reports")
def report(patient_id):
    p = get_patient(patient_id)
    r = get_reports(patient_id)
    return render_template("reports.html",patient=p,reports=r)

@app.route("/report/delete/<int:report_id>/<int:patient_id>/<filename>")
def remove_report(report_id,patient_id,filename):
    delete_reports(report_id,patient_id,filename)
    return redirect(url_for("report",patient_id=patient_id))

#MEDICATIONS
@app.route("/patient/<int:patient_id>/medications")
def medications(patient_id):
    p = get_patient(patient_id)
    meds = get_medications(patient_id)
    return render_template("medication.html",patient=p,medications=meds)

@app.route("/patient/<int:patient_id>/add_medication", methods = ["GET" , "POST"])
def add_med(patient_id):
    if request.method == "POST":
        name = request.form["name"]
        dose = request.form["dose"]
        frequency = request.form["frequency"]
        timing = request.form["timing"]
        add_medication(patient_id,name,dose,frequency,timing)
        return redirect(url_for("medications",patient_id=patient_id))
    return render_template("add_medication.html",patient_id = patient_id)

@app.route("/medication/delete/<int:medication_id>/<int:patient_id>")
def remove_medication(medication_id,patient_id):
    delete_medication(medication_id)
    return redirect(url_for("medications",patient_id = patient_id))

@app.route("/patient/<int:patient_id>/emergency")
def emergency(patient_id):
    p = get_patient(patient_id)
    summary = get_patient_summary(patient_id)
    messages = [
        {
            "role": "system",
            "content": """You are MedEx, a medical assistant. Based on the patient data provided, generate:
1. A list of emergency warning signs to watch for
2. Immediate steps to take if an emergency occurs
3. When to call an ambulance immediately

Be clear, simple, and practical. Use bullet points."""
        },
        {
            "role": "user",
            "content": f"Patient data:\n{summary}\n\nGenerate emergency warning signs and guidance for this patient."
        }
    ]
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    response = chat.choices[0].message.content
    return render_template("emergency.html", patient=p, response=response)


@app.route("/patient/<int:patient_id>/summary")
def visit_summary(patient_id):
    p = get_patient(patient_id)
    summary = get_patient_summary(patient_id)
    meds = get_medications(patient_id)
    med_list = "\n".join([f"- {m[2]} {m[3]} {m[4]} {m[5]}" for m in meds])
    messages = [
        {
            "role": "system",
            "content": """You are MedEx, a medical assistant. Generate a clean doctor visit summary that the patient can show to their doctor. Include:
1. Patient overview
2. Recent vitals trend
3. Current medications
4. Key concerns to discuss
5. Questions to ask the doctor

Keep it professional and concise."""
        },
        {
            "role": "user",
            "content": f"Patient data:\n{summary}\n\nMedications:\n{med_list}\n\nGenerate a doctor visit summary."
        }
    ]
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    response = chat.choices[0].message.content
    return render_template("summary.html", patient=p, response=response)

@app.route("/vital/delete/<int:vital_id>/<int:patient_id>")
def remove_vital(vital_id, patient_id):
    delete_vitals(vital_id)
    return redirect(url_for("view_vitals", patient_id=patient_id))


@app.route("/patient/<int:patient_id>/summary/pdf")
def download_summary(patient_id):
    p = get_patient(patient_id)
    summary = get_patient_summary(patient_id)
    meds = get_medications(patient_id)
    med_list = "\n".join([f"- {m[2]} {m[3]} {m[4]} {m[5]}" for m in meds])
    messages = [
        {
            "role": "system",
            "content": """You are MedEx, a medical assistant. Generate a clean doctor visit summary. Include:
1. Patient overview
2. Recent vitals trend
3. Current medications
4. Key concerns to discuss
5. Questions to ask the doctor
Keep it professional and concise."""
        },
        {
            "role": "user",
            "content": f"Patient data:\n{summary}\n\nMedications:\n{med_list}\n\nGenerate a doctor visit summary."
        }
    ]
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    response = chat.choices[0].message.content
    buf = generate_summary_pdf(p, response)
    return send_file(buf, as_attachment=True, download_name = f"{p[1]}_summary.pdf" , mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug = True)

