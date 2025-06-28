from nicegui import ui
from ..layout import layout
from ...schemas.service_worker_schema import ServiceWorkerCreate,ServiceWorkerUpdateAgent
from ...utils.db_context import db_context
from ...services.service_worker_service import (create_worker, update_worker,
    delete_worker, get_all_workers,update_worker_from_agent)
import socket
import json
import os

filters = {
    'status': '',
}

# Socket configuration for agent communication
def get_socket_path() -> str:
    """Get appropriate socket path for agent communication."""
    # Production: systemd managed socket
    prod_socket = "/run/devopin-agent.sock"
    if os.path.exists(prod_socket):
        return prod_socket
    
    # Development/fallback: use /tmp
    return "/tmp/devopin-agent.sock"

SOCKET_PATH = get_socket_path()
class AgentController:
    """Handler untuk komunikasi dengan devopin-agent via Unix socket"""
    
    @staticmethod
    def send_command(command: str, service_name: str|None = None) -> dict:
        """Send command to agent via Unix socket"""
        try:
            if not os.path.exists(SOCKET_PATH):
                return {"success": False, "message": "Agent socket not found. Is devopin-agent running?"}
            
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 second timeout
            
            sock.connect(SOCKET_PATH)
            
            # Prepare command
            cmd_data = {
                "command": command,
                "service": service_name
            }
            
            # Send command
            message = json.dumps(cmd_data) + "\n"
            sock.send(message.encode())
            
            # Receive response
            response = sock.recv(1024).decode()
            sock.close()
            
            return json.loads(response)
            
        except socket.timeout:
            return {"success": False, "message": "Command timeout. Agent may be busy."}
        except ConnectionRefusedError:
            return {"success": False, "message": "Cannot connect to agent. Is devopin-agent service running?"}
        except Exception as e:
            return {"success": False, "message": f"Error communicating with agent: {str(e)}"}

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
    agent_controller = AgentController()

    def load_workers():
        """Load semua workers dari database"""
        nonlocal service_workers, filtered_workers
        with db_context() as db:
            workers = get_all_workers(db)
            service_workers = [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description if w.description else "No description",
                    "status": w.status if w.status is not None else "inactive",
                    "is_enabled": getattr(w, "is_enabled", False),
                    "is_monitoring": getattr(w, "is_monitoring", False),
                }
                for w in workers
            ]
            filtered_workers = service_workers.copy()
            refresh_table()

    def filter_workers():
        """Filter workers berdasarkan search term dan status"""
        nonlocal filtered_workers
        filtered_workers = service_workers.copy()

        # Filter berdasarkan search term
        if search_term:
            term = search_term.lower()
            filtered_workers = [
                w for w in filtered_workers if (
                    term in w["name"].lower()
                    or (w.get("description") and term in w["description"].lower())
                    or term in w["status"].lower()
                )
            ]

        # Filter berdasarkan status
        if filters.get('status'):
            filtered_workers = [
                w for w in filtered_workers if w["status"] == filters["status"]
            ]

        refresh_table()

    def refresh_table():
        """Refresh table dengan data terbaru"""
        if table_element:
            table_element.rows = filtered_workers
            table_element.update()

    def clear_form():
        """Clear form data"""
        form_data.update({
            "id": None,
            "name": "",
            "description": "",
            "is_monitoring": False,
            "is_enabled": False,
            "status": "",
        })

    def open_add_dialog():
        """Open dialog untuk add worker"""
        clear_form()
        worker_dialog.open()
        dialog_title.text = "Add New Service Worker"
        save_button.text = "Create Service Worker"

    def open_edit_dialog(payload):
        """Open dialog untuk edit worker"""
        form_data.update(payload)
        name_input.value = payload["name"]
        description_input.value = payload["description"]
        worker_dialog.open()
        dialog_title.text = "Edit Service Worker"
        save_button.text = "Update Service Worker"

    def save_worker():
        """Save atau update worker"""
        try:
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
            ui.notify(f"Error saving worker: {str(e)}", type="negative")

    def delete_worker_handler(worker_id):
        """Delete worker dengan confirmation"""
        try:
            with db_context() as db:
                delete_worker(db, worker_id)
                ui.notify("Service worker deleted successfully!", type="positive")
                load_workers()
        except Exception as e:
            ui.notify(f"Error deleting service worker: {str(e)}", type="negative")

    def confirm_delete(worker):
        """Show confirmation dialog untuk delete"""
        with ui.dialog() as delete_dialog, ui.card().classes("p-6"):
            ui.label(f'Delete Worker "{worker["name"]}"?').classes("text-lg font-semibold mb-4")
            ui.label("This action cannot be undone.").classes("text-gray-600 mb-6")

            with ui.row().classes("gap-2 justify-end w-full"):
                ui.button("Cancel", on_click=delete_dialog.close).classes("bg-gray-500 text-white")
                ui.button(
                    "Delete",
                    on_click=lambda: (delete_worker_handler(worker["id"]), delete_dialog.close()),
                ).classes("bg-red-500 text-white")

        delete_dialog.open()

    def handle_service_action(action: str, worker: dict):
        """Handle service control actions (start/stop/restart)"""
        service_name = worker["name"]
        
        # Show loading state
        ui.notify(f"{action.capitalize()}ing {service_name}...", type="info")
        
        # Send command to agent
        result = agent_controller.send_command(action, service_name)
        status_update = 'active' if action in ['start', 'restart'] else 'inactive'
        if result.get("success"):
            ui.notify(f"Successfully {action}ed {service_name}", type="positive")
            # Refresh data after action
            with db_context() as db:
                update_worker_from_agent(db, service_name,ServiceWorkerUpdateAgent(
                name=worker["name"],
                description=worker.get("description", ""),
                is_monitoring=worker.get("is_monitoring", True),
                is_enabled=worker.get("is_enabled", True),status=status_update))
            load_workers()
        else:
            ui.notify(f"Failed to {action} {service_name}: {result.get('message', 'Unknown error')}", type="negative")

    def show_service_control_dialog(worker: dict):
        """Show service control dialog with start/stop/restart options"""
        with ui.dialog() as control_dialog, ui.card().classes("p-6 min-w-96"):
            ui.label(f'Control Service: {worker["name"]}').classes("text-xl font-semibold mb-4")
            
            # Current status display
            with ui.row().classes("items-center gap-2 mb-4"):
                status_color = "green" if worker["status"] == "active" else "red"
                ui.html(f'<div class="w-3 h-3 rounded-full bg-{status_color}-500"></div>')
                ui.label(f"Current Status: {worker['status'].title()}").classes("font-medium")
            
            ui.separator().classes("my-4")
            
            # Action buttons
            with ui.column().classes("gap-3 w-full"):
                # Start button
                start_btn = ui.button(
                    "Start Service",
                    icon="play_arrow",
                    on_click=lambda: (
                        handle_service_action("start", worker),
                        control_dialog.close()
                    )
                ).classes("w-full bg-green-500 hover:bg-green-600 text-white")
                
                # Stop button
                stop_btn = ui.button(
                    "Stop Service", 
                    icon="stop",
                    on_click=lambda: (
                        handle_service_action("stop", worker),
                        control_dialog.close()
                    )
                ).classes("w-full bg-red-500 hover:bg-red-600 text-white")
                
                # Restart button
                restart_btn = ui.button(
                    "Restart Service",
                    icon="refresh", 
                    on_click=lambda: (
                        handle_service_action("restart", worker),
                        control_dialog.close()
                    )
                ).classes("w-full bg-orange-500 hover:bg-orange-600 text-white")
                
                # Enable/disable buttons based on current status
                if worker["status"] == "active":
                    start_btn.disable()
                else:
                    stop_btn.disable()
                    restart_btn.disable()
            
            ui.separator().classes("my-4")
            
            # Close button
            ui.button("Close", on_click=control_dialog.close).classes("w-full bg-gray-500 text-white")

        control_dialog.open()

    def check_agent_status():
        """Check if devopin-agent is running"""
        result = agent_controller.send_command("status")
        if result.get("success"):
            return True, "Agent is running"
        else:
            return False, result.get("message", "Agent not responding")

    # Main UI
    ui.label("Service Worker Management").classes("text-2xl font-bold mb-6")

    # Agent status indicator
    with ui.card().classes("p-4 mb-4 w-full"):
        with ui.row().classes("items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                agent_status_icon = ui.html('<div class="w-3 h-3 rounded-full bg-gray-500"></div>')
                agent_status_label = ui.label("Checking agent status...").classes("font-medium")
            
            ui.button(
                "Check Agent", 
                icon="refresh",
                on_click=lambda: update_agent_status()
            ).classes("bg-blue-500 text-white")

    def update_agent_status():
        """Update agent status display"""
        is_running, message = check_agent_status()
        color = "green" if is_running else "red"
        agent_status_icon.content = f'<div class="w-3 h-3 rounded-full bg-{color}-500"></div>'
        agent_status_label.text = f"Devopin Agent: {message}"

    # Initialize agent status check
    update_agent_status()

    with ui.card().classes("p-6 w-full"):
        # Header section
        with ui.row().classes("items-center justify-between w-full mb-6"):
            ui.label("Worker List").classes("text-xl font-semibold")
            ui.button("Add Service Worker", icon="add", on_click=open_add_dialog).classes(
                "bg-blue-500 hover:bg-blue-600 text-white rounded-lg px-4 py-2 transition-colors"
            )

        # Search and filter section
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
                status_select = ui.select(
                    options=['active', 'inactive'],
                    label='Status',
                    on_change=filter_workers
                ).props('dense clearable').classes('w-32')
                status_select.bind_value_to(filters, 'status')
                
                ui.button('', icon='refresh', on_click=load_workers).props('color=primary outline dense').tooltip('Refresh')

        # Table section with enhanced actions
        columns = [
            {"name": "name", "label": "Worker Name", "field": "name", "align": "left", "sortable": True},
            {"name": "description", "label": "Description", "field": "description", "align": "left"},
            {"name": "status", "label": "Status", "field": "status", "align": "center"},
            {"name": "monitoring", "label": "Monitoring", "field": "is_monitoring", "align": "center"},
            {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
        ]

        table_element = ui.table(
            columns=columns, rows=filtered_workers, row_key="id", pagination=10
        ).classes("w-full")

        # Custom slots
        table_element.add_slot(
            "body-cell-status",
            """
            <q-td :props="props">
                <q-badge :color="props.value === 'active' ? 'green' : 'grey'" :label="props.value" />
            </q-td>
            """
        )

        table_element.add_slot(
            "body-cell-monitoring",
            """
            <q-td :props="props">
                <q-badge :color="props.value ? 'blue' : 'grey'" :label="props.value ? 'Enabled' : 'Disabled'" />
            </q-td>
            """
        )

        table_element.add_slot(
            "body-cell-actions",
            """
            <q-td :props="props">
                <q-btn flat round color="green" icon="settings" size="sm" 
                       @click="$parent.$emit('control', props.row)" 
                       title="Service Control" />
                <q-btn flat round color="blue" icon="edit" size="sm" 
                       @click="$parent.$emit('edit', props.row)" 
                       title="Edit" />
                <q-btn flat round color="red" icon="delete" size="sm" 
                       @click="$parent.$emit('delete', props.row)" 
                       title="Delete" />
            </q-td>
            """
        )

        # Event handlers
        table_element.on("control", lambda e: show_service_control_dialog(e.args))
        table_element.on("edit", lambda e: open_edit_dialog(e.args))
        table_element.on("delete", lambda e: confirm_delete(e.args))

    # Dialog untuk Add/Edit Worker
    with ui.dialog().props("persistent") as worker_dialog, ui.card().classes("p-6 min-w-96"):
        dialog_title = ui.label("Add New Service Worker").classes("text-xl font-semibold mb-4")

        with ui.column().classes("gap-4 w-full"):
            name_input = ui.input(label="Name *", placeholder="Enter service name").classes("w-full").props("outlined")
            description_input = ui.textarea(label="Description", placeholder="Enter description").classes("w-full").props("outlined")
            ui.label("* Required fields").classes("text-xs text-gray-500")

        ui.separator().classes("my-4")

        with ui.row().classes("gap-2 justify-end w-full"):
            ui.button("Cancel", on_click=worker_dialog.close).classes("bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors")
            save_button = ui.button("Create Worker", on_click=save_worker).classes("bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors")

    # Load initial data
    load_workers()
    layout()