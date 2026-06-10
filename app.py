from flask import Flask , render_template,request,redirect,url_for
from database import add_patient,get_all_patients,get_patient,delete_patient,add_vitals,get_vitals
from dotenv import load_dotenv
load_dotenv()


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


if __name__ == "__main__":
    app.run(debug = True)

