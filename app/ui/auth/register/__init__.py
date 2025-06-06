
from nicegui import ui, app
from .action_register import handle_register  # pastikan kamu punya handler ini

@ui.page('/register')
def register_page():
    with ui.row().classes('w-full h-screen justify-center items-center'):
        with ui.card().classes('w-full max-w-md p-6 shadow-2'):
            ui.label('Register').classes('text-h5 text-center mb-4')

            name_input = ui.input('Name').classes('w-full')
            email_input = ui.input('Email').classes('w-full')
            password_input = ui.input('Password', password=True).classes('w-full')

            msg_label = ui.label('').classes('text-red-500 text-sm')

            ui.button('Register', on_click=lambda: handle_register(
                name_input, email_input, password_input, msg_label)
            ).classes('w-full mt-4')

            ui.link('Already have an account? Login', '/login').classes('text-sm text-center mt-2 block')
