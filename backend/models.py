from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    email      = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)  # hashed
    role       = Column(String, nullable=False)   # "patient", "guardian", "doctor", "admin"
    created_at = Column(DateTime, default=datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"
    id          = Column(String, primary_key=True)   # auto-generated "P001"
    user_id     = Column(Integer, ForeignKey("users.id"))
    name        = Column(String, nullable=False)
    age         = Column(Integer)
    gender      = Column(String)
    blood_group = Column(String)
    phone       = Column(String)
    address     = Column(String)
    doctor_id   = Column(String, ForeignKey("doctors.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    user      = relationship("User")
    doctor    = relationship("Doctor", back_populates="patients")
    guardians = relationship("Guardian", back_populates="patient")

class Guardian(Base):
    __tablename__ = "guardians"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(String, ForeignKey("patients.id"))
    name       = Column(String, nullable=False)
    phone      = Column(String)
    relation   = Column(String)   # "son", "daughter", "spouse" etc
    email      = Column(String)

    user    = relationship("User")
    patient = relationship("Patient", back_populates="guardians")

class Doctor(Base):
    __tablename__ = "doctors"
    id             = Column(String, primary_key=True)  # "D001"
    user_id        = Column(Integer, ForeignKey("users.id"))
    name           = Column(String, nullable=False)
    specialization = Column(String)
    phone          = Column(String)
    email          = Column(String)

    user     = relationship("User")
    patients = relationship("Patient", back_populates="doctor")

class VitalReading(Base):
    __tablename__ = "vitals"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"))
    bpm        = Column(Float)
    spo2       = Column(Float)
    # motion data from MPU9250
    ax         = Column(Float, nullable=True)
    ay         = Column(Float, nullable=True)
    az         = Column(Float, nullable=True)
    gx         = Column(Float, nullable=True)
    gy         = Column(Float, nullable=True)
    gz         = Column(Float, nullable=True)
    fall_detected = Column(Boolean, default=False)
    activity   = Column(String, nullable=True)
    timestamp  = Column(DateTime, default=datetime.utcnow)
    

class Alert(Base):
    __tablename__ = "alerts"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    patient_id    = Column(String, ForeignKey("patients.id"))
    alert_type    = Column(String)
    anomaly_score = Column(Float)
    shap_reason   = Column(String)
    timestamp     = Column(DateTime, default=datetime.utcnow)
    resolved      = Column(Boolean, default=False)