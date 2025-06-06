from nicegui import ui, app
from app.ui.auth.login import login_page
from app.ui.auth.register import register_page
from app.ui.dashboard import dashboard
from app.ui.project import project
@ui.page("/")
def index():
    ui.navigate.to("/login")

ui.run(title="User Auth with NiceGUI", reload=True, storage_secret="rashasiiajdlka")
