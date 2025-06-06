
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def hash_password(password:str):
    return ph.hash(password=password)

def verify_password(hash_password: str, password: str):
    try:
        return ph.verify(hash=hash_password, password=password)
    except VerifyMismatchError:
        # Password is incorrect
        return False
