from nicegui import ui


@ui.page("/404")
def not_found_page():
    with ui.card().classes("absolute-center text-center w-96"):
        ui.icon("mdi-alert-circle", size="xl", color="red")
        ui.label("Halaman Tidak Ditemukan").classes("text-h4")
        ui.separator()
        ui.label("URL yang Anda minta tidak tersedia")
        with ui.row().classes("w-full justify-center"):
            ui.button("Beranda", on_click=lambda: ui.navigate.to("/"))
            ui.button("Kembali", on_click=lambda: ui.navigate.back())
