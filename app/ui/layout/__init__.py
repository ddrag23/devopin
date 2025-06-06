from nicegui import ui, app
from .sidebar_menu import sidebar_menu


def layout():
    user = app.storage.user.get("session")
    if not user:
        ui.navigate.to("/login")
        return
    current_path = ui.context.client.page.path
    with (
        ui.header(elevated=True)
        .style("""
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    """)
        .classes("items-center justify-between px-6 py-3")
    ):
        # Menu button dengan hover effect
        ui.button(icon="menu", on_click=lambda: left_drawer.toggle()).classes(
            "text-white hover:bg-white/20 transition-all duration-200 rounded-lg p-2"
        )

        # Logo/Brand dengan typography yang lebih baik
        with ui.row().classes("items-center gap-2"):
            ui.icon("code", size="lg").classes("text-white")
            ui.label("Devopin").classes("text-2xl font-bold text-white tracking-wide")

        # User dropdown dengan styling modern
        with ui.row().classes("items-center gap-3"):
            # Avatar placeholder
            with ui.dropdown_button(
                icon="account_circle",
                auto_close=True,
            ).classes(
                "text-white bg-white/10 hover:bg-white/20 transition-all duration-200 rounded-lg px-4 py-2"
            ):
                ui.item(
                    "Profile",
                    on_click=lambda: ui.notify("Profile clicked", type="info"),
                )
                ui.item(
                    "Settings",
                    on_click=lambda: ui.notify("Settings clicked", type="info"),
                )
                ui.separator()
                ui.item(
                    "Logout",
                    on_click=lambda: (
                        app.storage.user.clear(),
                        ui.navigate.to("/login"),
                    ),
                ).classes("text-red-500")

    # Left drawer dengan design card-based
    with ui.left_drawer(bottom_corner=True, fixed=False).style("""
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        border-right: 1px solid #e2e8f0;
    """) as left_drawer:
        # Navigation items dengan design simple
        with ui.column().classes("p-2 gap-1 w-full"):
            # Dashboard - Active state
            for item in sidebar_menu:
                with ui.row().classes(
                    f"items-center gap-3 p-3 mx-2 rounded-lg w-full text-white cursor-pointer {'bg-gray-800' if current_path == item['path'] else ''}"
                ):
                    ui.icon(item.get("icon", "home"), size="sm").classes(
                        "text-white"
                        if current_path == item["path"]
                        else "text-gray-600"
                    )
                    ui.link(
                        item.get("label", "Dashbooard"), item.get("path", "/dashboard")
                    ).classes(
                        f"font-medium no-underline flex-1 {'text-white' if current_path == item['path'] else 'text-gray-600'}"
                    )

                # Project

            # Analytics dengan dropdown (expandable)
            # with ui.row().classes(
            #     "items-center gap-3 p-3 mx-2 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors duration-150"
            # ):
            #     ui.icon("analytics", size="sm").classes("text-gray-600")
            #     ui.label("Analytics").classes("text-gray-600 font-medium flex-1")
            #     ui.icon("expand_more", size="sm").classes("text-gray-400")
            #
            # # Sub-menu untuk Analytics (indented)
            # with ui.column().classes("ml-8 gap-1"):
            #     with ui.row().classes(
            #         "items-center gap-3 p-2 mx-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors duration-150"
            #     ):
            #         ui.label("Reports").classes("text-gray-500 text-sm")
            #     with ui.row().classes(
            #         "items-center gap-3 p-2 mx-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors duration-150"
            #     ):
            #         ui.label("Statistics").classes("text-gray-500 text-sm")
            #
            # Customers

    # with (
    #     ui.footer()
    #     .style("""
    #     background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    #     border-top: 1px solid #4a5568;
    # """)
    #     .classes("py-4 px-6")
    # ):
    #     with ui.row().classes("items-center justify-between w-full"):
    #         with ui.column():
    #             ui.label("© 2024 Devopin").classes("text-gray-300 text-sm")
    #             ui.label("Built with ❤️ using NiceGUI").classes("text-gray-400 text-xs")
    #
    #         # Social links atau quick actions
    #         with ui.row().classes("gap-2"):
    #             ui.button(icon="help", color="gray").classes(
    #                 "text-gray-300 hover:text-white transition-colors duration-200"
    #             )
    #             ui.button(icon="info", color="gray").classes(
    #                 "text-gray-300 hover:text-white transition-colors duration-200"
    #             )
