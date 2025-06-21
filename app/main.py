from nicegui import ui, app
from app.ui.auth.login import login_page
from app.ui.auth.register import register_page
from app.ui.dashboard import dashboard
from app.ui.project import project
from app.ui.error_page import not_found_page
from app.ui.project.detail import detail
from app.ui.service_worker import service_worker # type: ignore
from app.api.route import router

app.include_router(router)
@ui.page("/")
def index():
    ui.navigate.to("/login")


ui.run(title="User Auth with NiceGUI", reload=True, storage_secret="rashasiiajdlka")
