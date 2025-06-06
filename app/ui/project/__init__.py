from nicegui import ui
from ..layout import layout
from ...schemas.project_schema import ProjectCreate
from ...utils.db_context import db_context
from ...services.project_service import (
    get_all_projects,
    create_project,
    update_project,
    delete_project,
)


@ui.page("/project")
def project():
    # State untuk manage data
    projects_data = []
    filtered_projects = []
    search_term = ""

    # Form state
    form_data = {
        "id": None,
        "name": "",
        "description": "",
        "log_path": "",
        "is_alert": False,
        "framework_type": "",
    }

    # UI Elements yang akan diupdate
    table_element = None
    search_input = None

    def load_projects():
        """Load semua projects dari database"""
        nonlocal projects_data, filtered_projects
        with db_context() as db:
            projects = get_all_projects(db)
            projects_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": getattr(p, "description", ""),
                    "log_path": p.log_path,
                    "framework_type": p.framework_type,
                    "is_alert": getattr(p, "is_alert", False),
                    "status": "Active" if getattr(p, "is_alert", False) else "Inactive",
                }
                for p in projects
            ]
            filtered_projects = projects_data.copy()
            refresh_table()

    def filter_projects():
        """Filter projects berdasarkan search term"""
        nonlocal filtered_projects
        if search_term:
            filtered_projects = [
                p
                for p in projects_data
                if search_term.lower() in p["name"].lower()
                or (
                    p["description"] is not None
                    and search_term.lower() in p["description"].lower()
                )
                or search_term.lower() in p["log_path"].lower()
                or search_term.lower() in p["framework_type"].lower()
            ]
        else:
            filtered_projects = projects_data.copy()
        refresh_table()

    def refresh_table():
        """Refresh table dengan data terbaru"""
        if table_element:
            table_element.rows = filtered_projects
            table_element.update()

    def clear_form():
        """Clear form data"""
        form_data.update(
            {
                "id": None,
                "name": "",
                "description": "",
                "log_path": "",
                "is_alert": False,
            }
        )

    def open_add_dialog():
        """Open dialog untuk add project"""
        clear_form()
        project_dialog.open()
        dialog_title.text = "Add New Project"
        save_button.text = "Create Project"

    def open_edit_dialog(project):
        """Open dialog untuk edit project"""
        form_data.update(project)

        # Update form inputs
        name_input.value = project["name"]
        description_input.value = project["description"]
        log_path_input.value = project["log_path"]
        alert_switch.value = project["is_alert"]
        framework_type.value = project["framework_type"]

        project_dialog.open()
        dialog_title.text = "Edit Project"
        save_button.text = "Update Project"

    def save_project():
        """Save atau update project"""
        try:
            # Validation
            if not name_input.value.strip():
                ui.notify("Project name is required!", type="negative")
                return

            if not log_path_input.value.strip():
                ui.notify("Log path is required!", type="negative")
                return
            if not log_path_input.value.strip():
                ui.notify("Framework Type is required!", type="negative")
                return

            with db_context() as db:
                project_data = {
                    "name": name_input.value.strip(),
                    "description": description_input.value.strip(),
                    "log_path": log_path_input.value.strip(),
                    "is_alert": alert_switch.value,
                    "framework_type": framework_type.value,
                }

                if form_data["id"]:  # Update
                    update_project(db, form_data["id"], ProjectCreate(**project_data))
                    ui.notify("Project updated successfully!", type="positive")
                else:  # Create
                    create_project(db, ProjectCreate(**project_data))
                    ui.notify("Project created successfully!", type="positive")

                project_dialog.close()
                load_projects()

        except Exception as e:
            ui.notify(f"Error saving project: {str(e)}", type="negative")

    def delete_project_handler(project_id):
        """Delete project dengan confirmation"""
        try:
            with db_context() as db:
                delete_project(db, project_id)
                ui.notify("Project deleted successfully!", type="positive")
                load_projects()
        except Exception as e:
            ui.notify(f"Error deleting project: {str(e)}", type="negative")

    def confirm_delete(project):
        """Show confirmation dialog untuk delete"""
        with ui.dialog() as delete_dialog, ui.card().classes("p-6"):
            ui.label(f'Delete Project "{project["name"]}"?').classes(
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
                        delete_project_handler(project["id"]),
                        delete_dialog.close(),
                    ),
                ).classes("bg-red-500 text-white")

        delete_dialog.open()

    # Main UI
    ui.label("Project Management").classes("text-2xl font-bold mb-6")

    with ui.card().classes("p-6 w-full"):
        # Header section
        with ui.row().classes("items-center justify-between w-full mb-6"):
            ui.label("Project List").classes("text-xl font-semibold")
            ui.button("Add Project", icon="add", on_click=open_add_dialog).classes(
                "bg-blue-500 hover:bg-blue-600 text-white rounded-lg px-4 py-2 transition-colors"
            )

        # Search section
        with ui.row().classes("items-center gap-4 mb-4 w-full"):

            def handle_search_change(e):
                nonlocal search_term
                search_term = e.value
                filter_projects()

            search_input = (
                ui.input(
                    placeholder="Search projects...",
                    on_change=handle_search_change,
                )
                .classes("flex-1")
                .props("clearable outlined")
            )

            ui.button("Refresh", icon="refresh", on_click=load_projects).classes(
                "bg-gray-500 hover:bg-gray-600 text-white rounded-lg px-4 py-2 transition-colors"
            )

        # Table section
        columns = [
            {
                "name": "name",
                "label": "Project Name",
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
            {
                "name": "log_path",
                "label": "Log Path",
                "field": "log_path",
                "align": "left",
            },
            {
                "name": "framework",
                "label": "Framework",
                "field": "framework_type",
                "align": "left",
            },
            {"name": "status", "label": "Status", "field": "status", "align": "center"},
            {
                "name": "actions",
                "label": "Actions",
                "field": "actions",
                "align": "center",
            },
        ]

        table_element = ui.table(
            columns=columns, rows=filtered_projects, row_key="id", pagination=10
        ).classes("w-full")

        # Custom slot untuk actions column
        table_element.add_slot(
            "body-cell-status",
            """
            <q-td :props="props">
                <q-badge :color="props.value === 'Active' ? 'green' : 'grey'" :label="props.value" />
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

    # Dialog untuk Add/Edit Project
    frameworks = ["laravel", "django", "flask", "express", "spring", "fastapi"]
    with (
        ui.dialog().props("persistent") as project_dialog,
        ui.card().classes("p-6 min-w-96"),
    ):
        dialog_title = ui.label("Add New Project").classes("text-xl font-semibold mb-4")

        with ui.column().classes("gap-4 w-full"):
            name_input = (
                ui.input(label="Project Name *", placeholder="Enter project name")
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

            log_path_input = (
                ui.input(label="Log Path *", placeholder="/path/to/logs")
                .classes("w-full")
                .props("outlined")
            )
            framework_type = (
                ui.select(
                    label="Framework Type *",
                    options=frameworks,
                    with_input=True,
                    on_change=lambda e: ui.notify(e.value),
                )
                .classes("w-full")
                .props("outlined")
            )

            alert_switch = ui.switch(text="Enable Alerts", value=False).classes("mb-2")

            ui.label("* Required fields").classes("text-xs text-gray-500")

        ui.separator().classes("my-4")

        # Dialog buttons
        with ui.row().classes("gap-2 justify-end w-full"):
            ui.button("Cancel", on_click=project_dialog.close).classes(
                "bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
            )

            save_button = ui.button("Create Project", on_click=save_project).classes(
                "bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
            )

    # Load initial data
    load_projects()

    # Apply layout
    layout()
