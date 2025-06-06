from nicegui import ui,app
from app.services.user_service import get_user_by_email
from app.utils import verify_password
from sqlalchemy.orm import Session
from app.utils.db_context import db_context as get_db
def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if user and verify_password(user.password,password):
        return user
    return None

def handle_login(email_input, password_input, msg_label):
    with get_db() as db:
        user = authenticate_user(db, email_input.value, password_input.value)
        if user:
            app.storage.user['session'] = {
                'id' : user.id,
                'name': user.name,
                'email': user.email,
            }  # Store user session
            ui.navigate.to("/dashboard")
        else:
            msg_label.text = "Invalid credentials"
