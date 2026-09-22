"""
Seeds reference data (NIST functions/subcategories, roles) and a demo
organization + admin user so the system is usable immediately after setup.

Run via `python -m app.db.seed`.
"""
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.db.init_db import init_db
from app.data.nist_csf_seed import NIST_FUNCTIONS, NIST_SUBCATEGORIES
from app.models.models import NistFunction, NistSubcategory, Role, Organization, AppUser, CloudAccount


def seed():
    init_db()
    db = SessionLocal()
    try:
        if not db.query(NistFunction).first():
            for fn in NIST_FUNCTIONS:
                db.add(NistFunction(**fn))
            for sc in NIST_SUBCATEGORIES:
                db.add(NistSubcategory(**sc))

        if not db.query(Role).first():
            db.add_all([
                Role(role_id="admin", role_name="Administrator"),
                Role(role_id="engineer", role_name="Security Engineer"),
                Role(role_id="executive", role_name="Executive / Read-Only"),
            ])

        db.commit()

        org = db.query(Organization).filter(Organization.org_name == "Demo Corp").first()
        if not org:
            org = Organization(org_name="Demo Corp", industry="Financial Services")
            db.add(org)
            db.commit()
            db.refresh(org)

        if not db.query(AppUser).filter(AppUser.email == "admin@governx.local").first():
            db.add(AppUser(
                org_id=org.org_id,
                email="admin@governx.local",
                hashed_password=hash_password("ChangeMe123!"),
                role_id="admin",
            ))
        if not db.query(AppUser).filter(AppUser.email == "ciso@governx.local").first():
            db.add(AppUser(
                org_id=org.org_id,
                email="ciso@governx.local",
                hashed_password=hash_password("ChangeMe123!"),
                role_id="executive",
            ))

        if not db.query(CloudAccount).filter(CloudAccount.org_id == org.org_id).first():
            db.add(CloudAccount(org_id=org.org_id, provider="aws", account_identifier="demo-aws-account-001"))

        db.commit()
        print(f"Seed complete. Demo org_id={org.org_id}")
        print("Login: admin@governx.local / ChangeMe123!  (role: admin)")
        print("Login: ciso@governx.local  / ChangeMe123!  (role: executive)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
