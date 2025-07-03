from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..schemas.user_schema import UserCreate, UserResponse, UserUpdate, UserPasswordUpdate
from ..models.user import User as UserModel
from datetime import datetime, timezone
from ..utils import hash_password, verify_password


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


def update_user(db: Session, user_id: int, user_data: UserUpdate) -> UserResponse:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # Update only provided fields
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        # Check email uniqueness
        existing_user = db.query(UserModel).filter(
            UserModel.email == user_data.email,
            UserModel.id != user_id
        ).first()
        if existing_user:
            raise ValueError("Email already exists")
        user.email = user_data.email
    if user_data.user_timezone is not None:
        user.user_timezone = user_data.user_timezone
    
    user.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already exists")


def update_user_password(db: Session, user_id: int, password_data: UserPasswordUpdate) -> bool:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # Verify current password
    if not verify_password(password_data.current_password, user.password):
        raise ValueError("Current password is incorrect")
    
    # Update password
    user.password = hash_password(password_data.new_password)
    user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    return True


def get_users_count(db: Session) -> int:
    return db.query(UserModel).count()


def get_users_excluding_current(db: Session, current_user_id: int, skip: int = 0, limit: int = 100) -> list[UserModel]:
    return db.query(UserModel).filter(UserModel.id != current_user_id).offset(skip).limit(limit).all()


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
