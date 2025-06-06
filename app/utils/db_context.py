
# app/utils/db_context.py
from contextlib import contextmanager
from app.core.database import get_db

@contextmanager
def db_context():
    db_gen = get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        db_gen.close()
