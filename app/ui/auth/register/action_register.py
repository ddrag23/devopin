from nicegui import ui, app
from app.services.user_service import create_user
from app.utils.db_context import db_context as get_db
from app.schemas.user_schema import UserCreate
def handle_register(name_input, email_input, password_input, msg_label):
    with get_db() as db:
        try:
            create_user(db, UserCreate(name=name_input.value, email=email_input.value, password=password_input.value))
            msg_label.text = "Registered successfully! Redirecting..."
            ui.timer(1.5, lambda: ui.navigate.to("/login"))
        except ValueError as e:
            msg_label.text = str(e)
