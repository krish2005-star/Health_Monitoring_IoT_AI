from backend.database import SessionLocal
from backend.models import User
from backend.auth import hash_password

db = SessionLocal()

try:
    hashed_password = hash_password("12345678")

    db.query(User).update(
        {User.password: hashed_password},
        synchronize_session=False
    )

    db.commit()
    print("✅ All user passwords reset to 12345678")

except Exception as e:
    db.rollback()
    print(e)

finally:
    db.close()