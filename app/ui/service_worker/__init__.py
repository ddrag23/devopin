from nicegui import ui
from ..layout import layout
from ...schemas.service_worker_schema import ServiceWorkerCreate, ServiceWorkerUpdateAgent
from ...utils.db_context import db_context
from ...services.service_worker_service import (
    create_worker, update_worker, delete_worker, get_all_workers, update_worker_from_agent
)
from ...utils.agent_controller import AgentController

# Global variables for UI elements
service_worker_table = None
current_page = 1
current_limit = 10
total_count = 0

def get_status_color(status: str) -> str:
    """Get color based on service status"""
    colors = {
        'active': '#10b981',   # Emerald 500
        'inactive': '#ef4444', # Red 500
        'unknown': 'gray'
    }
    return colors.get(status.lower(), 'gray')

def get_status_icon(status: str) -> str:
    """Get icon based on service status"""
    icons = {
        'active': 'check_circle',
        'inactive': 'cancel',
        'unknown': 'help'
    }
    return icons.get(status.lower(), 'help')

async def handle_create_service_worker():
    """Show create service worker dialog"""
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Create New Service Worker').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Service Name').classes('w-full mb-2').props('outlined')
        description_input = ui.textarea('Description').classes('w-full mb-4').props('outlined')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def create_action():
                try:
                    if not name_input.value.strip():
                        ui.notify("Service worker name is required!", type="negative")
                        return
                    
                    with db_context() as db:
                        payload = ServiceWorkerCreate(
                            name=name_input.value.strip(),
                            description=description_input.value.strip()
                        )
                        create_worker(db, payload)
                        ui.notify("Service worker created successfully!", type="positive")
                        refresh_service_worker_data()
                        dialog.close()
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Create', on_click=create_action).props('color=primary')
    
    dialog.open()

async def handle_edit_service_worker(worker_id: int):
    """Show edit service worker dialog"""
    # Fetch current worker data
    with db_context() as db:
        workers = get_all_workers(db)
        worker_data = next((w for w in workers if w.id == worker_id), None)
    
    if not worker_data:
        ui.notify("Service worker not found", type="negative")
        return
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Edit Service Worker').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Service Name', value=worker_data.name).classes('w-full mb-2').props('outlined')
        description_input = ui.textarea('Description', value=worker_data.description or '').classes('w-full mb-4').props('outlined')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def update_action():
                try:
                    if not name_input.value.strip():
                        ui.notify("Service worker name is required!", type="negative")
                        return
                    
                    with db_context() as db:
                        payload = ServiceWorkerCreate(
                            name=name_input.value.strip(),
                            description=description_input.value.strip()
                        )
                        update_worker(db, worker_id, payload)
                        ui.notify("Service worker updated successfully!", type="positive")
                        refresh_service_worker_data()
                        dialog.close()
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Update', on_click=update_action).props('color=primary')
    
    dialog.open()

async def handle_delete_service_worker(worker_id: int, worker_name: str):
    """Show delete confirmation dialog"""
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Delete Service Worker: {worker_name}').classes('text-lg font-bold mb-4')
        ui.label('Are you sure you want to delete this service worker? This action cannot be undone.').classes('mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def delete_action():
                try:
                    with db_context() as db:
                        delete_worker(db, worker_id)
                        ui.notify("Service worker deleted successfully!", type="positive")
                        refresh_service_worker_data()
                        dialog.close()
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Delete', on_click=delete_action).props('color=red')
    
    dialog.open()

async def handle_service_control(action: str, worker: dict):
    """Handle service control actions (start/stop/restart)"""
    service_name = worker["name"]
    agent_controller = AgentController()
    
    # Show loading state
    ui.notify(f"{action.capitalize()}ing {service_name}...", type="info")
    
    # Send command to agent
    result = agent_controller.send_command(action, service_name)
    status_update = 'active' if action in ['start', 'restart'] else 'inactive'
    
    if result.get("success"):
        ui.notify(f"Successfully {action}ed {service_name}", type="positive")
        # Refresh data after action
        with db_context() as db:
            update_worker_from_agent(db, service_name, ServiceWorkerUpdateAgent(
                name=worker["name"],
                description=worker.get("description", ""),
                is_monitoring=worker.get("is_monitoring", True),
                is_enabled=worker.get("is_enabled", True),
                status=status_update
            ))
        refresh_service_worker_data()
    else:
        ui.notify(f"Failed to {action} {service_name}: {result.get('message', 'Unknown error')}", type="negative")

async def show_service_control_dialog(worker: dict):
    """Show service control dialog"""
    
    async def handle_control_action(action: str):
        """Handle service control action and close dialog"""
        dialog.close()
        await handle_service_control(action, worker)
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label(f'Control Service: {worker["name"]}').classes('text-lg font-bold mb-4')
        
        # Current status
        with ui.row().classes('items-center gap-2 mb-4'):
            ui.icon(get_status_icon(worker["status"])).classes(f"text-{get_status_color(worker['status'])}-500")
            ui.label(f"Status: {worker['status'].title()}").classes('font-medium')
        
        # Action buttons
        with ui.column().classes('w-full gap-2'):
            start_btn = ui.button(
                'Start Service',
                icon='play_arrow',
                on_click=lambda: handle_control_action('start')
            ).classes('w-full')
            
            stop_btn = ui.button(
                'Stop Service',
                icon='stop',
                on_click=lambda: handle_control_action('stop')
            ).classes('w-full').props('color=red')
            
            restart_btn = ui.button(
                'Restart Service',
                icon='refresh',
                on_click=lambda: handle_control_action('restart')
            ).classes('w-full').props('color=amber')
            
            # Enable/disable buttons based on status
            if worker["status"] == "active":
                start_btn.disable()
            else:
                stop_btn.disable()
                restart_btn.disable()
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Close', on_click=dialog.close).props('flat')
    
    dialog.open()

def refresh_service_worker_data():
    """Refresh service worker table"""
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
        update_service_worker_table(service_workers)

def update_service_worker_table(workers):
    """Update the service worker table with new data"""
    global service_worker_table
    
    if service_worker_table:
        service_worker_table.clear()
        
        if not workers:
            with service_worker_table:
                ui.label("No service workers found").classes("text-center text-gray-500 p-4")
            return
        
        with service_worker_table:
            # Table header
            with ui.row().classes("w-full bg-gray-100 p-3 rounded-t-lg font-bold text-sm"):
                ui.label("Name").classes("flex-1")
                ui.label("Description").classes("flex-1")
                ui.label("Status").classes("w-24 text-center")
                ui.label("Monitoring").classes("w-24 text-center")
                ui.label("Actions").classes("w-40 text-center")
            
            # Table rows
            for worker in workers:
                with ui.row().classes("w-full border-b border-gray-200 p-3 hover:bg-gray-50 items-center"):
                    # Name
                    with ui.column().classes("flex-1"):
                        ui.label(worker["name"]).classes("font-medium text-sm")
                    
                    # Description
                    with ui.column().classes("flex-1"):
                        ui.label(worker["description"]).classes("text-sm text-gray-600")
                    
                    # Status
                    with ui.element('div').classes("w-24 flex justify-center"):
                        ui.chip(
                            worker["status"].title(),
                            color=get_status_color(worker["status"])
                        ).classes("text-xs text-white")
                    
                    # Monitoring
                    with ui.element('div').classes("w-24 flex justify-center"):
                        monitoring_color = "#10b981" if worker["is_monitoring"] else "gray"
                        monitoring_text = "Enabled" if worker["is_monitoring"] else "Disabled"
                        ui.chip(monitoring_text, color=monitoring_color).classes("text-xs text-white")
                    
                    # Actions
                    with ui.row().classes("w-40 justify-center gap-1"):
                        # Control button
                        ui.button(
                            icon="settings",
                            on_click=lambda e,w=worker: show_service_control_dialog(w)
                        ).classes("text-emerald-600 hover:bg-emerald-100 p-1").props("flat dense size=sm").tooltip("Control")
                        
                        # Edit button
                        ui.button(
                            icon="edit",
                            on_click=lambda e,w=worker: handle_edit_service_worker(w["id"])
                        ).classes("text-blue-500 hover:bg-blue-50 p-1").props("flat dense size=sm").tooltip("Edit")
                        
                        # Delete button
                        ui.button(
                            icon="delete",
                            on_click=lambda e,w=worker: handle_delete_service_worker(w["id"], w["name"])
                        ).classes("text-red-600 hover:bg-red-100 p-1").props("flat dense size=sm").tooltip("Delete")

async def handle_search(search_text: str):
    """Handle search functionality"""
    refresh_service_worker_data()

@ui.page("/service-worker")
def service_worker():
    """Service worker management page"""
    global service_worker_table
    
    ui.add_css('''
        .service-worker-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .service-worker-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
    ''')
    
    with ui.column().classes('service-worker-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('🔧 Service Worker Management').classes('text-3xl font-bold')
            
            # Actions and filters
            with ui.row().classes('items-center gap-3'):
                search_input = ui.input(
                    placeholder="Search service workers...",
                    on_change=lambda e: handle_search(e.value)
                ).classes('w-64')
                search_input.props('clearable outlined dense')
                
                ui.button(
                    icon="add",
                    text="New Worker",
                    on_click=handle_create_service_worker
                ).classes("bg-blue-600 text-white hover:bg-blue-700")
                
                ui.button(
                    icon="refresh",
                    on_click=refresh_service_worker_data
                ).classes("p-2").tooltip("Refresh")
        
        # Main service worker table
        with ui.card().classes('service-worker-card w-full'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Service Workers').classes('text-xl font-semibold')
                    
                    # Info text
                    ui.label('Manage and control your service workers').classes('text-sm text-gray-600')
                
                # Service worker table container
                service_worker_table = ui.column().classes("w-full")
    
    # Load initial data
    refresh_service_worker_data()
    
    # Add layout
    layout()