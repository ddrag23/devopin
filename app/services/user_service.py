from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..schemas.user_schema import UserCreate, UserResponse
from ..models.user import User as UserModel
from datetime import datetime
from ..utils import hash_password


def create_user(db: Session, user_data: UserCreate) -> UserResponse:
    hashed = hash_password(user_data.password)
    user = UserModel(
        name=user_data.name,
        email=user_data.email,
        password=hashed,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")


def get_user_by_id(db: Session, user_id: int) -> UserResponse:
    return db.query(UserModel).filter(UserModel.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> UserModel | None:
    return db.query(UserModel).filter(UserModel.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[UserModel]:
    return db.query(UserModel).offset(skip).limit(limit).all()


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
