from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from .serial_reader import start_serial_thread, sensor_status, latest_bpm
from . import models, schemas
from .database import engine, get_db
from .auth import hash_password, verify_password, create_token, get_current_user, require_role
from .alerts import send_alerts
from .report import generate_report
from ml.predict import get_anomaly_score, load_artifacts, patient_buffers
from ml.shap_explain import get_shap_plot, load_shap

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    print("Loading ML artifacts...")
    load_artifacts()

    print("Loading SHAP...")
    load_shap()

    print("Starting serial thread...")
    start_serial_thread()

# ─── AUTH ────────────────────────────────────────────────

@app.post("/register/patient", tags=["auth"])
def register_patient(data: schemas.RegisterPatient,
                     db: Session = Depends(get_db)):
    if db.query(models.User)\
         .filter(models.User.email == data.email).first():
        raise HTTPException(400, "Email already registered")

    # create user account
    user = models.User(
        email    = data.email,
        password = hash_password(data.password),
        role     = "patient"
    )
    db.add(user)
    db.flush()

    # generate patient ID
    count = db.query(models.Patient).count()
    pid   = f"P{count+1:03d}"

    patient = models.Patient(
        id          = pid,
        user_id     = user.id,
        name        = data.name,
        age         = data.age,
        gender      = data.gender,
        blood_group = data.blood_group,
        phone       = data.phone,
        address     = data.address,
        doctor_id   = data.doctor_id or None,
    )
    db.add(patient)
    db.flush()

    # create guardian record
    # NOTE: guardians may not have an account/password at signup. To avoid
    # assigning the patient's password to the guardian (previous behavior),
    # we create a guardian profile without creating a linked User entry.
    # If you want guardians to have login accounts, create a separate flow
    # to collect/assign passwords or generate a secure temporary password.
    guardian = models.Guardian(
        user_id    = None,
        patient_id = pid,
        name       = data.guardian_name,
        phone      = data.guardian_phone,
        email      = data.guardian_email,
        relation   = data.guardian_relation,
    )
    db.add(guardian)
    db.commit()

    return {"message": "Registered successfully", "patient_id": pid}

@app.post("/register/doctor", tags=["auth"])
def register_doctor(data: schemas.RegisterDoctor,
                    db: Session = Depends(get_db)):
    if db.query(models.User)\
         .filter(models.User.email == data.email).first():
        raise HTTPException(400, "Email already registered")

    user = models.User(
        email    = data.email,
        password = hash_password(data.password),
        role     = "doctor"
    )
    db.add(user)
    db.flush()

    count = db.query(models.Doctor).count()
    did   = f"D{count+1:03d}"

    doctor = models.Doctor(
        id             = did,
        user_id        = user.id,
        name           = data.name,
        specialization = data.specialization,
        phone          = data.phone,
        email          = data.email,
    )
    db.add(doctor)
    db.commit()
    return {"message": "Doctor registered", "doctor_id": did}

@app.post("/login", response_model=schemas.TokenOut, tags=["auth"])
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User)\
             .filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid credentials")

    # get display name based on role
    name = user.email
    if user.role == "patient":
        p = db.query(models.Patient)\
              .filter(models.Patient.user_id == user.id).first()
        if p: name = p.name
    elif user.role == "doctor":
        d = db.query(models.Doctor)\
              .filter(models.Doctor.user_id == user.id).first()
        if d: name = d.name
    elif user.role == "guardian":
        g = db.query(models.Guardian)\
              .filter(models.Guardian.user_id == user.id).first()
        if g: name = g.name

    token = create_token({"user_id": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer",
            "role": user.role, "name": name}

# ─── PATIENT ROUTES ──────────────────────────────────────

@app.get("/me/vitals", tags=["patient"])
def my_vitals(current_user=Depends(require_role("patient")),
              db: Session = Depends(get_db)):
    patient = db.query(models.Patient)\
                .filter(models.Patient.user_id == current_user.id).first()
    return db.query(models.VitalReading)\
             .filter(models.VitalReading.patient_id == patient.id)\
             .order_by(models.VitalReading.timestamp.desc())\
             .limit(100).all()

@app.get("/me/alerts", tags=["patient"])
def my_alerts(current_user=Depends(require_role("patient")),
              db: Session = Depends(get_db)):
    patient = db.query(models.Patient)\
                .filter(models.Patient.user_id == current_user.id).first()
    return db.query(models.Alert)\
             .filter(models.Alert.patient_id == patient.id)\
             .order_by(models.Alert.timestamp.desc()).all()

@app.get("/me/profile", tags=["patient"])
def my_profile(current_user=Depends(require_role("patient")),
               db: Session = Depends(get_db)):
    patient = db.query(models.Patient)\
                .filter(models.Patient.user_id == current_user.id).first()
    guardians = db.query(models.Guardian)\
                  .filter(models.Guardian.patient_id == patient.id).all()
    doctor = None
    if patient.doctor_id:
        doctor = db.query(models.Doctor)\
                   .filter(models.Doctor.id == patient.doctor_id).first()
    return {
        "patient":   patient,
        "guardians": guardians,
        "doctor":    doctor
    }

# ─── GUARDIAN ROUTES ─────────────────────────────────────

@app.get("/guardian/patient", tags=["guardian"])
def guardian_view(current_user=Depends(require_role("guardian")),
                  db: Session = Depends(get_db)):
    guardian = db.query(models.Guardian)\
                 .filter(models.Guardian.user_id == current_user.id).first()
    patient  = db.query(models.Patient)\
                 .filter(models.Patient.id == guardian.patient_id).first()
    vitals   = db.query(models.VitalReading)\
                 .filter(models.VitalReading.patient_id == patient.id)\
                 .order_by(models.VitalReading.timestamp.desc())\
                 .limit(100).all()
    alerts   = db.query(models.Alert)\
                 .filter(models.Alert.patient_id == patient.id)\
                 .order_by(models.Alert.timestamp.desc()).all()
    return {"patient": patient, "vitals": vitals, "alerts": alerts}

# ─── DOCTOR ROUTES ───────────────────────────────────────

@app.get("/doctor/patients", tags=["doctor"])
def doctor_patients(current_user=Depends(require_role("doctor")),
                    db: Session = Depends(get_db)):
    doctor   = db.query(models.Doctor)\
                 .filter(models.Doctor.user_id == current_user.id).first()
    patients = db.query(models.Patient)\
                 .filter(models.Patient.doctor_id == doctor.id).all()
    return patients

@app.get("/doctor/patient/{patient_id}", tags=["doctor"])
def doctor_patient_detail(patient_id: str,
                           current_user=Depends(require_role("doctor")),
                           db: Session = Depends(get_db)):
    doctor  = db.query(models.Doctor)\
                .filter(models.Doctor.user_id == current_user.id).first()
    patient = db.query(models.Patient)\
                .filter(models.Patient.id == patient_id,
                        models.Patient.doctor_id == doctor.id).first()
    if not patient:
        raise HTTPException(404, "Patient not found or not under your care")

    vitals = db.query(models.VitalReading)\
               .filter(models.VitalReading.patient_id == patient_id)\
               .order_by(models.VitalReading.timestamp.desc())\
               .limit(100).all()
    alerts = db.query(models.Alert)\
               .filter(models.Alert.patient_id == patient_id)\
               .order_by(models.Alert.timestamp.desc()).all()
    return {"patient": patient, "vitals": vitals, "alerts": alerts}

# ─── ADMIN ROUTES ────────────────────────────────────────

@app.get("/admin/patients", tags=["admin"])
def all_patients(current_user=Depends(require_role("admin")),
                 db: Session = Depends(get_db)):
    return db.query(models.Patient).all()

@app.get("/admin/doctors", tags=["admin"])
def all_doctors(current_user=Depends(require_role("admin")),
                db: Session = Depends(get_db)):
    return db.query(models.Doctor).all()

# ─── VITALS (ESP32 / simulator) ──────────────────────────

from ml.fall_detection import detect_fall, classify_activity_motion

@app.post("/vitals", tags=["sensors"])
def receive_vitals(data: schemas.VitalIn,
                   db: Session = Depends(get_db)):

    # fall detection
    fall_detected, fall_reason = detect_fall(
        data.ax, data.ay, data.az,
        data.gx or 0, data.gy or 0, data.gz or 0
    )

    # activity classification
    activity = classify_activity_motion(data.bpm, data.ax, data.ay, data.az)

    # save reading
    reading = models.VitalReading(
        patient_id    = data.patient_id,
        bpm           = data.bpm,
        spo2          = data.spo2,
        ax=data.ax, ay=data.ay, az=data.az,
        gx=data.gx, gy=data.gy, gz=data.gz,
        fall_detected = fall_detected,
        activity      = activity,
    )
    db.add(reading)
    db.commit()

    # anomaly detection
    score, reason = get_anomaly_score(data.patient_id, data.bpm, data.spo2)

    # fire alert if: high anomaly score OR fall detected OR low SpO2
    should_alert = score > 0.75 or fall_detected or data.spo2 < 94

    if should_alert:
        alert_type = "fall_detected" if fall_detected else \
                     "spo2_critical" if data.spo2 < 94 else "bpm_anomaly"
        final_reason = fall_reason if fall_detected else reason

        alert = models.Alert(
            patient_id    = data.patient_id,
            alert_type    = alert_type,
            anomaly_score = score,
            shap_reason   = final_reason
        )
        db.add(alert)
        db.commit()

        send_alerts(data.patient_id, data.bpm, data.spo2,
                    final_reason, alert_type, db)

    return {
        "status":        "ok",
        "anomaly_score": round(score, 3),
        "activity":      activity,
        "fall_detected": fall_detected
    }

@app.get("/vitals/{patient_id}", tags=["sensors"])
def get_vitals(patient_id: str, db: Session = Depends(get_db)):
    return db.query(models.VitalReading)\
             .filter(models.VitalReading.patient_id == patient_id)\
             .order_by(models.VitalReading.timestamp.desc())\
             .limit(100).all()

@app.get("/alerts/{patient_id}", tags=["sensors"])
def get_alerts(patient_id: str, db: Session = Depends(get_db)):
    return db.query(models.Alert)\
             .filter(models.Alert.patient_id == patient_id)\
             .order_by(models.Alert.timestamp.desc()).all()

@app.get("/report/{patient_id}", tags=["reports"])
def download_report(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(models.Patient)\
                .filter(models.Patient.id == patient_id).first()
    vitals  = db.query(models.VitalReading)\
                .filter(models.VitalReading.patient_id == patient_id)\
                .order_by(models.VitalReading.timestamp).all()
    alerts  = db.query(models.Alert)\
                .filter(models.Alert.patient_id == patient_id).all()
    pdf = generate_report(patient, vitals, alerts)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f"attachment; filename=report_{patient_id}.pdf"})

@app.get("/shap/{patient_id}", tags=["ml"])
def shap_chart(patient_id: str):
    buf = patient_buffers.get(patient_id, [])
    img = get_shap_plot(buf)
    if not img:
        raise HTTPException(404, "Not enough data")
    return Response(content=img, media_type="image/png")

@app.get("/doctors/list", tags=["auth"])
def list_doctors(db: Session = Depends(get_db)):
    return db.query(models.Doctor).all()

@app.get("/admin/patients-simple", tags=["admin"])
def patients_simple(db: Session = Depends(get_db)):
    """public endpoint for simulator — returns id + base_bpm only"""
    patients = db.query(models.Patient).all()
    return [{"id": p.id, "base_bpm": 72} for p in patients]

@app.get("/sensor/status", tags=["sensors"])
def sensor_status_check():
    return {"status": sensor_status, "bpm": latest_bpm}