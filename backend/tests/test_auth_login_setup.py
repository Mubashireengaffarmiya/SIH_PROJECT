import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal, User, Base, engine
from routers.auth import ensure_demo_users


def test_ensure_demo_users_creates_default_accounts():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(User).delete()
        db.commit()

        ensure_demo_users(db=db)

        usernames = {user.username for user in db.query(User).all()}
        assert {"inspector", "reviewer", "admin"}.issubset(usernames)
    finally:
        db.close()



