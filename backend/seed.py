from backend.database import SessionLocal, engine, Base
from backend.models import Patient

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def run():
    db = SessionLocal()
    patients = [
        Patient(id="A001", name="Ramesh Kumar", age=68, contact="+91XXXXXXXXXX"),
        Patient(id="B002", name="Lakshmi Devi", age=72, contact="+91XXXXXXXXXX"),
        Patient(id="C003", name="Ahmed Khan",   age=65, contact="+91XXXXXXXXXX"),
    ]
    for p in patients:
        # merge will insert or update by primary key
        db.merge(p)
    db.commit()
    db.close()
    print("Patients added.")


if __name__ == '__main__':
    run()
