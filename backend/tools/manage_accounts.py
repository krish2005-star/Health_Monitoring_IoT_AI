#!/usr/bin/env python3
"""Admin utility: list accounts and optionally reset passwords for testing.

USAGE examples:
  # list users
  python backend/tools/manage_accounts.py --list

  # reset all user passwords to a known test password (DEV ONLY)
  python backend/tools/manage_accounts.py --reset-all --password changeme123

This script intentionally does NOT print hashed passwords. Passwords are stored
hashed in the DB and cannot be recovered. Use --reset-all to set a new password
for all users (useful in local/dev environments).
"""
import argparse
from backend.database import SessionLocal
from backend import models
from backend.auth import hash_password


def list_users(db):
    users = db.query(models.User).all()
    if not users:
        print("No users found.")
        return
    print(f"{'id':<6} {'email':<30} {'role':<10} {'name':<20}")
    print('-'*72)
    for u in users:
        # user may relate to patient/doctor/guardian for name lookups
        name = getattr(u, 'name', '') or ''
        # attempt to resolve related records
        if u.role == 'patient':
            p = db.query(models.Patient).filter(models.Patient.user_id == u.id).first()
            if p:
                name = p.name
        elif u.role == 'doctor':
            d = db.query(models.Doctor).filter(models.Doctor.user_id == u.id).first()
            if d:
                name = d.name
        elif u.role == 'guardian':
            g = db.query(models.Guardian).filter(models.Guardian.user_id == u.id).first()
            if g:
                name = g.name

        print(f"{u.id:<6} {getattr(u,'email',''):<30} {u.role:<10} {name:<20}")


def reset_all_passwords(db, new_password):
    if not new_password:
        raise ValueError("new_password must be provided")
    users = db.query(models.User).all()
    for u in users:
        u.password = hash_password(new_password)
        db.add(u)
    db.commit()
    print(f"Reset password for {len(users)} users.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--list', action='store_true', help='List all users')
    p.add_argument('--reset-all', action='store_true', help='Reset password for all users (DEV ONLY)')
    p.add_argument('--password', type=str, help='New password to set when using --reset-all')
    args = p.parse_args()

    db = SessionLocal()
    try:
        if args.list or (not args.reset_all and not args.list):
            list_users(db)
        if args.reset_all:
            # safety: require explicit password
            if not args.password:
                print('Error: --password is required with --reset-all')
            else:
                reset_all_passwords(db, args.password)
                print('Passwords reset. Use the new password to log in.')
    finally:
        db.close()


if __name__ == '__main__':
    main()
