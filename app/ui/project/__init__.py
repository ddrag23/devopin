from nicegui import ui
from ..layout import layout
from ...schemas.project_schema import ProjectCreate
from ...utils.db_context import db_context
from ...services.project_service import (
    get_all_projects,
    create_project,
    update_project,
    delete_project,
    get_project_by_id,
)

# Global variables for UI elements
project_table = None
current_page = 1
current_limit = 10
total_count = 0

def get_status_color(is_alert: bool) -> str:
    """Get color based on alert status"""
    return 'green' if is_alert else 'gray'

def get_status_text(is_alert: bool) -> str:
    """Get text based on alert status"""
    return 'Enabled' if is_alert else 'Disabled'

def get_framework_icon(framework: str) -> str:
    """Get icon based on framework type"""
    icons = {
        'laravel': 'code',
        'python': 'code',
        'django': 'web',
        'flask': 'web',
        'express': 'javascript',
        'spring': 'coffee',
        'fastapi': 'rocket_launch'
    }
    return icons.get(framework.lower(), 'folder')

async def handle_create_project():
    """Show create project dialog"""
    frameworks = ["laravel", "python", "django", "flask", "express", "spring", "fastapi"]
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Create New Project').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Project Name').classes('w-full mb-2').props('outlined')
        description_input = ui.textarea('Description').classes('w-full mb-2').props('outlined')
        log_path_input = ui.input('Log Path').classes('w-full mb-2').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            framework_select = ui.select(
                frameworks,
                label='Framework Type',
                value='python'
            ).classes('flex-1').props('outlined')
            
            alert_switch = ui.switch('Enable Alerts', value=False).classes('mt-4')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def create_action():
                try:
                    if not name_input.value.strip():
                        ui.notify("Project name is required!", type="negative")
                        return
                    
                    if not log_path_input.value.strip():
                        ui.notify("Log path is required!", type="negative")
                        return
                    
                    with db_context() as db:
                        payload = ProjectCreate(
                            name=name_input.value.strip(),
                            description=description_input.value.strip(),
                            log_path=log_path_input.value.strip(),
                            framework_type=framework_select.value,
                            is_alert=alert_switch.value
                        )
                        create_project(db, payload)
                        ui.notify("Project created successfully!", type="positive")
                        refresh_project_data()
                        dialog.close()
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Create', on_click=create_action).props('color=primary')
    
    dialog.open()

async def handle_edit_project(project_id: int):
    """Show edit project dialog"""
    frameworks = ["laravel", "python", "django", "flask", "express", "spring", "fastapi"]
    
    # Fetch current project data
    with db_context() as db:
        project_data = get_project_by_id(db, project_id)
    
    if not project_data:
        ui.notify("Project not found", type="negative")
        return
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Edit Project').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Project Name', value=project_data.name).classes('w-full mb-2').props('outlined')
        description_input = ui.textarea('Description', value=project_data.description or '').classes('w-full mb-2').props('outlined')
        log_path_input = ui.input('Log Path', value=project_data.log_path).classes('w-full mb-2').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            framework_select = ui.select(
                frameworks,
                label='Framework Type',
                value=project_data.framework_type
            ).classes('flex-1').props('outlined')
            
            alert_switch = ui.switch('Enable Alerts', value=getattr(project_data, 'is_alert', False)).classes('mt-4')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def update_action():
                try:
                    if not name_input.value.strip():
                        ui.notify("Project name is required!", type="negative")
                        return
                    
                    if not log_path_input.value.strip():
                        ui.notify("Log path is required!", type="negative")
                        return
                    
                    with db_context() as db:
                        payload = ProjectCreate(
                            name=name_input.value.strip(),
                            description=description_input.value.strip(),
                            log_path=log_path_input.value.strip(),
                            framework_type=framework_select.value,
                            is_alert=alert_switch.value
                        )
                        update_project(db, project_id, payload)
                        ui.notify("Project updated successfully!", type="positive")
                        refresh_project_data()
                        dialog.close()
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Update', on_click=update_action).props('color=primary')
    
    dialog.open()

async def handle_delete_project(project_id: int, project_name: str):
    """Show delete confirmation dialog"""
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Delete Project: {project_name}').classes('text-lg font-bold mb-4')
        ui.label('Are you sure you want to delete this project? This action cannot be undone.').classes('mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def delete_action():
                try:
                    with db_context() as db:
                        delete_project(db, project_id)
                        ui.notify("Project deleted successfully!", type="positive")
                        refresh_project_data()
                        dialog.close()
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Delete', on_click=delete_action).props('color=red')
    
    dialog.open()

def refresh_project_data():
    """Refresh project table"""
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
            }
            for p in projects
        ]
        update_project_table(projects_data)

def update_project_table(projects):
    """Update the project table with new data"""
    global project_table
    
    if project_table:
        project_table.clear()
        
        if not projects:
            with project_table:
                ui.label("No projects found").classes("text-center text-gray-500 p-4")
            return
        
        with project_table:
            # Table header
            with ui.row().classes("w-full bg-gray-100 p-3 rounded-t-lg font-bold text-sm"):
                ui.label("Project").classes("flex-1")
                ui.label("Framework").classes("w-32 text-center")
                ui.label("Log Path").classes("w-64")
                ui.label("Alerts").classes("w-24 text-center")
                ui.label("Actions").classes("w-40 text-center")
            
            # Table rows
            for project in projects:
                with ui.row().classes("w-full border-b border-gray-200 p-3 hover:bg-gray-50 items-center"):
                    # Project info
                    with ui.column().classes("flex-1"):
                        ui.label(project["name"]).classes("font-medium text-sm")
                        if project["description"]:
                            ui.label(project["description"]).classes("text-xs text-gray-600 mt-1")
                    
                    # Framework
                    with ui.element('div').classes("w-32 flex justify-center items-center"):
                        ui.icon(get_framework_icon(project["framework_type"])).classes("text-blue-500 mr-2")
                        ui.label(project["framework_type"].title()).classes("text-sm")
                    
                    # Log Path
                    with ui.element('div').classes("w-64"):
                        ui.label(project["log_path"]).classes("text-sm font-mono text-gray-600")
                    
                    # Alerts
                    with ui.element('div').classes("w-24 flex justify-center"):
                        ui.chip(
                            get_status_text(project["is_alert"]),
                            color=get_status_color(project["is_alert"])
                        ).classes("text-xs")
                    
                    # Actions
                    with ui.row().classes("w-40 justify-center gap-1"):
                        # View details button
                        ui.button(
                            icon="visibility",
                            on_click=lambda p=project: ui.navigate.to(f"/project/{p['id']}/detail")
                        ).classes("text-green-600 hover:bg-green-100 p-1").props("flat dense size=sm").tooltip("View Details")
                        
                        # Edit button
                        ui.button(
                            icon="edit",
                            on_click=lambda p=project: handle_edit_project(p["id"])
                        ).classes("text-blue-600 hover:bg-blue-100 p-1").props("flat dense size=sm").tooltip("Edit")
                        
                        # Delete button
                        ui.button(
                            icon="delete",
                            on_click=lambda p=project: handle_delete_project(p["id"], p["name"])
                        ).classes("text-red-600 hover:bg-red-100 p-1").props("flat dense size=sm").tooltip("Delete")

async def handle_search(search_text: str):
    """Handle search functionality"""
    refresh_project_data()

@ui.page("/project")
def project():
    """Project management page"""
    global project_table
    
    ui.add_css('''
        .project-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .project-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
    ''')
    
    with ui.column().classes('project-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('📁 Project Management').classes('text-3xl font-bold')
            
            # Actions and filters
            with ui.row().classes('items-center gap-3'):
                search_input = ui.input(
                    placeholder="Search projects...",
                    on_change=lambda e: handle_search(e.value)
                ).classes('w-64')
                search_input.props('clearable outlined dense')
                
                ui.button(
                    icon="add",
                    text="New Project",
                    on_click=handle_create_project
                ).classes("bg-blue-500 text-white")
                
                ui.button(
                    icon="refresh",
                    on_click=refresh_project_data
                ).classes("p-2").tooltip("Refresh")
        
        # Main project table
        with ui.card().classes('project-card w-full'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Projects').classes('text-xl font-semibold')
                    
                    # Info text
                    ui.label('Manage your application projects and monitoring settings').classes('text-sm text-gray-600')
                
                # Project table container
                project_table = ui.column().classes("w-full")
    
    # Load initial data
    refresh_project_data()
    
    # Add layout
    layout()