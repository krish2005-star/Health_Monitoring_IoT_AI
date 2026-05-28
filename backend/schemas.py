from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Auth
class RegisterPatient(BaseModel):
    name:        str
    email:       EmailStr
    password:    str
    age:         int
    gender:      str
    blood_group: str
    phone:       str
    address:     str
    # guardian details
    guardian_name:     str
    guardian_phone:    str
    guardian_email:    EmailStr
    guardian_relation: str
    # doctor (optional)
    doctor_id: Optional[str] = None

class RegisterDoctor(BaseModel):
    name:           str
    email:          EmailStr
    password:       str
    specialization: str
    phone:          str

class LoginIn(BaseModel):
    email:    str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    name:         str

# Vitals
class VitalIn(BaseModel):
    patient_id: str
    bpm:        float
    spo2:       float
    ax: Optional[float] = None
    ay: Optional[float] = None
    az: Optional[float] = None
    gx: Optional[float] = None
    gy: Optional[float] = None
    gz: Optional[float] = None

class VitalOut(BaseModel):
    patient_id:    str
    bpm:           float
    spo2:          float
    fall_detected: Optional[bool] = False
    activity:      Optional[str]  = None
    timestamp:     datetime
    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    patient_id:    str
    alert_type:    str
    anomaly_score: float
    shap_reason:   str
    timestamp:     datetime
    resolved:      bool
    class Config:
        from_attributes = True

class PatientOut(BaseModel):
    id:          str
    name:        str
    age:         int
    gender:      str
    blood_group: str
    phone:       str
    doctor_id:   Optional[str]
    class Config:
        from_attributes = True

class DoctorOut(BaseModel):
    id:             str
    name:           str
    specialization: str
    phone:          str
    email:          str
    class Config:
        from_attributes = True