import uuid
from sqlalchemy import create_engine, select, desc, Date
from sqlalchemy.orm import Session, sessionmaker
from models import Base, Users
from datetime import date

engine = create_engine('sqlite:///./size_detector.db', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base.metadata.create_all(engine)


def upsert_user(name: str, email: str, weight: float = None, gender: str = None, height: int = None,
                date_of_birth: date = None) -> dict:
    email = email.strip().lower()
    name = name.strip().lower() or 'Unknown'
    with SessionLocal() as db:
        try:
            u = db.scalar(select(Users).where(Users.email == email))
            if u:
                if name:
                    u.name = u.name.strip() or u.name
            else:
                u = Users(public_id=str(uuid.uuid4()), name=name.strip(), email=email,
                          height=height, weight=weight, gender=gender, date_of_birth=date_of_birth)
                db.add(u)
            db.commit()
            db.refresh(u)
            return {'id': u.id, "public_id": u.public_id, 'name': u.name, 'email': u.email}
        except Exception:
            db.rollback()
            raise Exception


def list_users() -> list:
    with SessionLocal() as ses:
        rows = ses.scalars(select(Users).order_by(desc(Users.id))).all()
        return [
            {'id': u.id, "public_id": u.public_id, 'name': u.name, 'email': u.email}
            for u in rows
        ]


def delete_user(public_id: str) -> bool:
    with SessionLocal() as ses:
        try:
            u = ses.scalar(select(Users).where(Users.public_id == public_id))
            if not u:
                return False
            ses.delete(u)
            ses.commit()
            return True
        except Exception as e:
            ses.rollback()
            raise Exception(e)


def get_user_by_public_id(public_id: str) -> dict:
    with SessionLocal() as ses:
        u = ses.scalar(select(Users).where(Users.public_id == public_id))
    if not u:
        return None
    return {'id': u.id, 'public_id': u.public_id, 'name': u.name, 'email': u.email}


if __name__ == '__main__':
    all_users = list_users()
    for user in all_users:
        print(user)
