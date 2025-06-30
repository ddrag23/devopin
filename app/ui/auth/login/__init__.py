from nicegui import ui, app
from .action_login import handle_login

@ui.page('/login')
def login_page():
    with ui.row().classes('w-full h-screen justify-center items-center'):
        with ui.card().classes('w-full max-w-md p-6 shadow-2'):
            ui.label("Login").classes("text-2xl text-center mb-4")
            email = ui.input("Email").classes("w-full mb-4")
            password = ui.input("Password", password=True).classes("w-full mb-4")
            msg = ui.label('').classes('text-red-500 text-sm')

            ui.button("Login", on_click=lambda: handle_login(email, password, msg)).classes("bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700")
            ui.link("Don't have an account? Register", "/register")
