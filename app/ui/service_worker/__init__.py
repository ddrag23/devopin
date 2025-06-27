from nicegui import ui
from ..layout import layout
from ...schemas.service_worker_schema import ServiceWorkerCreate
from ...utils.db_context import db_context
from ...services.service_worker_service import (create_worker, update_worker,
    delete_worker,get_all_workers)

filters = {
    'status': '',
    }
@ui.page("/service-worker")
def service_worker():
    # State untuk manage data
    service_workers = []
    filtered_workers = []
    search_term = ""

    # Form state
    form_data = {
        "id": None,
        "name": "",
        "description": "",
        "is_monitoring": False,
        "is_enabled": False,
        "status": "",
    }

    # UI Elements yang akan diupdate
    table_element = None

    def load_workers():
        """Load semua projects dari database"""
        nonlocal service_workers, filtered_workers
        with db_context() as db:
            projects = get_all_workers(db)
            service_workers = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description if p.description else "No description",
                    "status": p.status if p.status is not None else "Worker Inactive",
                    "is_enabled": getattr(p, "is_enabled", False),
                    "is_monitoring": getattr(p, "is_monitoring", False),
                }
                for p in projects
            ]
            filtered_workers = service_workers.copy()
            refresh_table()

    def filter_workers():
        """Filter projects berdasarkan search term"""
        nonlocal filtered_workers
        filtered_workers = service_workers.copy()

        # Filter berdasarkan search term
        if search_term:
            term = search_term.lower()
            filtered_workers = [
                p for p in filtered_workers if (
                    term in p["name"].lower()
                    or (p.get("description") and term in p["description"].lower())
                    or term in p["status"].lower()
                )
            ]

        # Filter berdasarkan status
        if filters.get('status'):
            filtered_workers = [
                p for p in filtered_workers if p["status"] == filters["status"]
            ]

        refresh_table()

    def refresh_table():
        """Refresh table dengan data terbaru"""
        if table_element:
            table_element.rows = filtered_workers
            table_element.update()
    def clear_form():
        """Clear form data"""
        form_data.update(
            {
                "id": None,
                "name": "",
                "description": "",
                "is_monitoring": False,
                "is_enabled": False,
                "status": "",
            }
        )

    def open_add_dialog():
        """Open dialog untuk add project"""
        clear_form()
        worker_dialog.open()
        dialog_title.text = "Add New Service Worker"
        save_button.text = "Create Service Worker"

    def open_edit_dialog(payload):
        """Open dialog untuk edit payload"""
        form_data.update(payload)

        # Update form inputs
        name_input.value = payload["name"]
        description_input.value = payload["description"]

        worker_dialog.open()
        dialog_title.text = "Edit Project"
        save_button.text = "Update Project"

    def save_worker():
        """Save atau update project"""
        try:
            # Validation
            if not name_input.value.strip():
                ui.notify("Service worker name is required!", type="negative")
                return

            with db_context() as db:
                payload_input = {
                    "name": name_input.value.strip(),
                    "description": description_input.value.strip(),
                }

                if form_data["id"]:  # Update
                    update_worker(db, form_data["id"], ServiceWorkerCreate(**payload_input))
                    ui.notify("Service worker updated successfully!", type="positive")
                else:  # Create
                    create_worker(db, ServiceWorkerCreate(**payload_input))
                    ui.notify("Service worker created successfully!", type="positive")

                worker_dialog.close()
                load_workers()

        except Exception as e:
            ui.notify(f"Error saving project: {str(e)}", type="negative")

    def delete_worker_handler(project_id):
        """Delete project dengan confirmation"""
        try:
            with db_context() as db:
                delete_worker(db, project_id)
                ui.notify("Service worker deleted successfully!", type="positive")
                load_workers()
        except Exception as e:
            ui.notify(f"Error deleting service worker: {str(e)}", type="negative")

    def confirm_delete(project):
        """Show confirmation dialog untuk delete"""
        with ui.dialog() as delete_dialog, ui.card().classes("p-6"):
            ui.label(f'Delete Worker "{project["name"]}"?').classes(
                "text-lg font-semibold mb-4"
            )
            ui.label("This action cannot be undone.").classes("text-gray-600 mb-6")

            with ui.row().classes("gap-2 justify-end w-full"):
                ui.button("Cancel", on_click=delete_dialog.close).classes(
                    "bg-gray-500 text-white"
                )
                ui.button(
                    "Delete",
                    on_click=lambda: (
                        delete_worker_handler(project["id"]),
                        delete_dialog.close(),
                    ),
                ).classes("bg-red-500 text-white")

        delete_dialog.open()
        
    # Main UI
    ui.label("Service Worker Management").classes("text-2xl font-bold mb-6")

    with ui.card().classes("p-6 w-full"):
        # Header section
        with ui.row().classes("items-center justify-between w-full mb-6"):
            ui.label("Worker List").classes("text-xl font-semibold")
            ui.button("Add Service Worker", icon="add", on_click=open_add_dialog).classes(
                "bg-blue-500 hover:bg-blue-600 text-white rounded-lg px-4 py-2 transition-colors"
            )

        # Search section
        with ui.row().classes("items-center flex justify-between mb-4 w-full"):

            def handle_search_change(e):
                nonlocal search_term
                search_term = e.value
                filter_workers()

            ui.input(
                placeholder="Search worker...",
                on_change=handle_search_change,
            ).classes("w-1/4").props("clearable dense")
            with ui.row().classes('gap-2 items-center'):
                            
                # Log level filter
                status_select = ui.select(
                    options=['active', 'inactive'],
                    label='Status',
                    on_change=filter_workers
                ).props('dense clearable').classes('w-32')
                status_select.bind_value_to(filters, 'status')
                
                ui.button(
                    '',
                    icon='refresh',
                    on_click=filter_workers
                ).props('color=primary outline dense').tooltip('Refresh')
            

        # Table section
        columns = [
            {
                "name": "name",
                "label": "Worker Name",
                "field": "name",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "description",
                "label": "Description",
                "field": "description",
                "align": "left",
            },
            {"name": "status", "label": "Worker Status", "field": "status", "align": "center"},
            {
                "name": "actions",
                "label": "Actions",
                "field": "actions",
                "align": "center",
            },
        ]

        table_element = ui.table(
            columns=columns, rows=filtered_workers, row_key="id", pagination=10
        ).classes("w-full")

        # Custom slot untuk actions column
        table_element.add_slot(
            "body-cell-status",
            """
            <q-td :props="props">
                <q-badge :color="props.value === 'active' ? 'green' : 'grey'" :label="props.value" />
            </q-td>
        """,
        )

        table_element.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
                <q-btn flat round color="blue" icon="edit" size="sm" 
                       @click="$parent.$emit('edit', props.row)" />
                <q-btn flat round color="red" icon="delete" size="sm" 
                       @click="$parent.$emit('delete', props.row)" />
            </q-td>
        """,
        )

        # Event handlers untuk table actions
        table_element.on("edit", lambda e: open_edit_dialog(e.args))
        table_element.on("delete", lambda e: confirm_delete(e.args))
        table_element.on(
            "detail", lambda e: ui.navigate.to(f"project/{e.args['id']}/detail")
        )

    # Dialog untuk Add/Edit Project
    with (
        ui.dialog().props("persistent") as worker_dialog,
        ui.card().classes("p-6 min-w-96"),
    ):
        dialog_title = ui.label("Add New Service Worker").classes("text-xl font-semibold mb-4")

        with ui.column().classes("gap-4 w-full"):
            name_input = (
                ui.input(label="Name *", placeholder="Enter name")
                .classes("w-full")
                .props("outlined")
            )

            description_input = (
                ui.textarea(
                    label="Description", placeholder="Enter project description"
                )
                .classes("w-full")
                .props("outlined")
            )

            ui.label("* Required fields").classes("text-xs text-gray-500")

        ui.separator().classes("my-4")

        # Dialog buttons
        with ui.row().classes("gap-2 justify-end w-full"):
            ui.button("Cancel", on_click=worker_dialog.close).classes(
                "bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
            )

            save_button = ui.button("Create Project", on_click=save_worker).classes(
                "bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
            )

    # Load initial data
    load_workers()

    # Apply layout
    layout()
