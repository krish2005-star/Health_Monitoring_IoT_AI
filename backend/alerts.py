import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

FAST2SMS_KEY = "2BYIsGtLlFuhXZKngJkyiqvrP3pdm48E1x6TAHjaDceNU0z7VOKDFP9ixb5ryc1HvgJf0AUSR3L7NmGn"

GMAIL_USER   = "m.krishna0513@gmail.com"
GMAIL_PASS   = "wofx hacn npqh obop"   # Gmail App Password (16 chars)

import geocoder  # pip install geocoder

def get_approximate_location() -> str:
    """get approximate location from IP address"""
    try:
        g = geocoder.ip('me')
        if g.ok:
            return f"{g.city}, {g.state}, {g.country}"
    except:
        pass
    return "Location unavailable"

def send_alerts(patient_id: str, bpm: float, spo2: float,
                reason: str, alert_type: str, db):
    from models import Patient, Guardian, Doctor
    patient   = db.query(Patient).filter(Patient.id == patient_id).first()
    guardians = db.query(Guardian).filter(Guardian.patient_id == patient_id).all()
    doctor    = None
    if patient and patient.doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == patient.doctor_id).first()

    location = get_approximate_location()
    patient_name = patient.name if patient else patient_id

    # build alert emoji based on type
    emoji = "🚨" if alert_type == "fall_detected" else \
            "💔" if alert_type == "bpm_anomaly" else "😮‍💨"

    recipients = [{"name": g.name, "phone": g.phone,
                   "email": g.email, "relation": g.relation}
                  for g in guardians]
    if doctor:
        recipients.append({"name": f"Dr. {doctor.name}",
                            "phone": doctor.phone,
                            "email": doctor.email,
                            "relation": "Doctor"})

    for r in recipients:
        _send_sms(r["phone"], patient_name, bpm, spo2,
                  reason, alert_type, location)
        _send_email(r["email"], r["name"], patient_name,
                    bpm, spo2, reason, alert_type, location)


def _send_sms(to_phone, patient_name, bpm, spo2,
              reason, alert_type, location):
    try:
        # Fast2SMS needs 10-digit number without +91
        number = to_phone.replace("+91", "").replace(" ", "").strip()

        alert_label = {
            "fall_detected": "FALL DETECTED",
            "bpm_anomaly":   "HEART RATE EMERGENCY",
            "spo2_critical": "LOW OXYGEN EMERGENCY"
        }.get(alert_type, "EMERGENCY")

        message = (
            f"EMERGENCY - {alert_label}\n"
            f"Patient: {patient_name}\n"
            f"BPM: {bpm} | SpO2: {spo2}%\n"
            f"Reason: {reason}\n"
            f"Location: {location}\n"
            f"Time: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}\n"
            f"Please check immediately!"
        )

        response = requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={"authorization": FAST2SMS_KEY},
            json={
                "route":   "q",
                "message": message,
                "numbers": number
            }
        )
        result = response.json()
        if result.get("return"):
            print(f"SMS sent to {to_phone}")
        else:
            print(f"Fast2SMS error: {result}")
    except Exception as e:
        print(f"SMS error: {e}")

def _send_email(to_email, to_name, patient_name,
                bpm, spo2, reason, alert_type, location):
    try:
        alert_label = {
            "fall_detected": "FALL DETECTED",
            "bpm_anomaly":   "HEART RATE EMERGENCY",
            "spo2_critical": "LOW OXYGEN EMERGENCY"
        }.get(alert_type, "EMERGENCY")

        color = "#dc2626" if alert_type == "bpm_anomaly" else \
                "#ea580c" if alert_type == "fall_detected" else "#7c3aed"

        em = MIMEMultipart()
        em['From']    = GMAIL_USER
        em['To']      = to_email
        em['Subject'] = f"EMERGENCY: {alert_label} — {patient_name}"
        html = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:auto">
          <div style="background:{color};color:white;
                      padding:20px;border-radius:8px 8px 0 0">
            <h2 style="margin:0">{alert_label}</h2>
            <p style="margin:4px 0 0;opacity:0.85">HealthMonitor AI System</p>
          </div>
          <div style="background:#f8fafc;padding:20px;
                      border-radius:0 0 8px 8px">
            <p>Dear {to_name},</p>
            <table style="width:100%;border-collapse:collapse">
              <tr>
                <td style="padding:8px;color:#6b7280;width:40%">Patient</td>
                <td style="padding:8px;font-weight:600">{patient_name}</td>
              </tr>
              <tr style="background:white">
                <td style="padding:8px;color:#6b7280">Heart Rate</td>
                <td style="padding:8px;font-weight:600;
                           color:{color}">{bpm} BPM</td>
              </tr>
              <tr>
                <td style="padding:8px;color:#6b7280">SpO2</td>
                <td style="padding:8px;font-weight:600">{spo2}%</td>
              </tr>
              <tr style="background:white">
                <td style="padding:8px;color:#6b7280">Alert Type</td>
                <td style="padding:8px;font-weight:600;
                           color:{color}">{alert_label}</td>
              </tr>
              <tr>
                <td style="padding:8px;color:#6b7280">Reason</td>
                <td style="padding:8px">{reason}</td>
              </tr>
              <tr style="background:white">
                <td style="padding:8px;color:#6b7280">Location</td>
                <td style="padding:8px">
                  <a href="https://maps.google.com/?q={location}"
                     style="color:#2563eb">{location}</a>
                </td>
              </tr>
              <tr>
                <td style="padding:8px;color:#6b7280">Time</td>
                <td style="padding:8px">
                  {datetime.now().strftime('%d %b %Y, %H:%M:%S')}
                </td>
              </tr>
            </table>
            <div style="margin-top:16px;padding:12px;background:#fef2f2;
                        border-radius:6px;border-left:4px solid {color}">
              <p style="margin:0;font-size:13px;color:#991b1b">
                Please check on the patient immediately or
                call emergency services if needed.
              </p>
            </div>
          </div>
        </div>
        """
        em.attach(MIMEText(html, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.sendmail(GMAIL_USER, to_email, em.as_string())
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Email error: {e}")