from nicegui import ui, app
from ..layout import layout


@ui.page("/dashboard")
def dashboard():
    user = app.storage.user.get("session", {})
    ui.label(f"Welcome, {user.get('name')}").classes("text-xl")
    layout()
