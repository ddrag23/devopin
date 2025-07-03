from nicegui import ui, app
from ..layout import layout
from ...schemas.user_schema import UserCreate, UserUpdate
from ...utils.db_context import db_context
from ...services.user_service import (
    get_users_excluding_current,
    create_user,
    update_user,
    delete_user,
    get_user_by_id,
    get_users_count,
)

# Global variables for UI elements
user_table = None
current_page = 1
current_limit = 10
total_count = 0

# Available timezones
TIMEZONES = [
    'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Phoenix',
    'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
    'Europe/Rome', 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata', 'Asia/Dubai',
    'Australia/Sydney', 'Pacific/Auckland'
]

def get_current_user_id():
    """Get current logged in user ID"""
    user_session = app.storage.user.get("session")
    return user_session.get('id') if user_session else None

def get_status_color(is_active: bool) -> str:
    """Get color based on status"""
    return '#10b981' if is_active else 'gray'  # Emerald 500

def get_role_icon() -> str:
    """Get icon for user role"""
    return 'person'

async def handle_create_user():
    """Show create user dialog"""
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Create New User').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Full Name').classes('w-full mb-2').props('outlined')
        email_input = ui.input('Email Address').classes('w-full mb-2').props('outlined')
        password_input = ui.input('Password', password=True).classes('w-full mb-2').props('outlined')
        confirm_password_input = ui.input('Confirm Password', password=True).classes('w-full mb-2').props('outlined')
        
        timezone_select = ui.select(
            TIMEZONES,
            label='Timezone',
            value='UTC'
        ).classes('w-full mb-4').props('outlined')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def create_action():
                try:
                    if not name_input.value or not name_input.value.strip():
                        ui.notify("Full name is required!", type="negative")
                        return
                    
                    if not email_input.value or not email_input.value.strip():
                        ui.notify("Email address is required!", type="negative")
                        return
                    
                    if not password_input.value or len(password_input.value) < 6:
                        ui.notify("Password must be at least 6 characters!", type="negative")
                        return
                    
                    if password_input.value != confirm_password_input.value:
                        ui.notify("Passwords do not match!", type="negative")
                        return
                    
                    with db_context() as db:
                        payload = UserCreate(
                            name=name_input.value.strip(),
                            email=email_input.value.strip().lower(),
                            password=password_input.value,
                            user_timezone=timezone_select.value
                        )
                        create_user(db, payload)
                        ui.notify("User created successfully!", type="positive")
                        refresh_user_data()
                        dialog.close()
                except ValueError as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
                except Exception as e:
                    ui.notify(f"Unexpected error: {str(e)}", type="negative")
            
            ui.button('Create', on_click=create_action).props('color=primary')
    
    dialog.open()

async def handle_edit_user(user_id: int):
    """Show edit user dialog"""
    
    # Fetch current user data
    with db_context() as db:
        user_data = get_user_by_id(db, user_id)
    
    if not user_data:
        ui.notify("User not found", type="negative")
        return
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Edit User').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Full Name', value=user_data.name).classes('w-full mb-2').props('outlined')
        email_input = ui.input('Email Address', value=user_data.email).classes('w-full mb-2').props('outlined')
        
        timezone_select = ui.select(
            TIMEZONES,
            label='Timezone',
            value=user_data.user_timezone or 'UTC'
        ).classes('w-full mb-4').props('outlined')
        
        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def update_action():
                try:
                    if not name_input.value or not name_input.value.strip():
                        ui.notify("Full name is required!", type="negative")
                        return
                    
                    if not email_input.value or not email_input.value.strip():
                        ui.notify("Email address is required!", type="negative")
                        return
                    
                    with db_context() as db:
                        payload = UserUpdate(
                            name=name_input.value.strip(),
                            email=email_input.value.strip().lower(),
                            user_timezone=timezone_select.value
                        )
                        update_user(db, user_id, payload)
                        ui.notify("User updated successfully!", type="positive")
                        refresh_user_data()
                        dialog.close()
                except ValueError as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
                except Exception as e:
                    ui.notify(f"Unexpected error: {str(e)}", type="negative")
            
            ui.button('Update', on_click=update_action).props('color=primary')
    
    dialog.open()

async def handle_delete_user(user_id: int, user_name: str):
    """Show delete confirmation dialog"""
    current_user_id = get_current_user_id()
    
    if user_id == current_user_id:
        ui.notify("You cannot delete your own account!", type="negative")
        return
    
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Delete User: {user_name}').classes('text-lg font-bold mb-4')
        ui.label('Are you sure you want to delete this user? This action cannot be undone.').classes('mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            def delete_action():
                try:
                    with db_context() as db:
                        delete_user(db, user_id)
                        ui.notify("User deleted successfully!", type="positive")
                        refresh_user_data()
                        dialog.close()
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Delete', on_click=delete_action).props('color=red')
    
    dialog.open()

def refresh_user_data():
    """Refresh user table"""
    current_user_id = get_current_user_id()
    if not current_user_id:
        ui.notify("Session expired. Please login again.", type="negative")
        ui.navigate.to('/login')
        return
    
    with db_context() as db:
        users = get_users_excluding_current(db, current_user_id)
        users_data = [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "user_timezone": u.user_timezone or 'UTC',
                "created_at": u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else 'N/A',
                "updated_at": u.updated_at.strftime('%Y-%m-%d %H:%M') if u.updated_at else 'N/A',
            }
            for u in users
        ]
        update_user_table(users_data)

def update_user_table(users):
    """Update the user table with new data"""
    global user_table
    
    if user_table:
        user_table.clear()
        
        if not users:
            with user_table:
                ui.label("No users found").classes("text-center text-gray-500 p-4")
            return
        
        with user_table:
            # Table header
            with ui.row().classes("w-full bg-gray-100 p-3 rounded-t-lg font-bold text-sm"):
                ui.label("User").classes("flex-1")
                ui.label("Email").classes("w-64")
                ui.label("Timezone").classes("w-32 text-center")
                ui.label("Created").classes("w-32 text-center")
                ui.label("Actions").classes("w-32 text-center")
            
            # Table rows
            for user in users:
                with ui.row().classes("w-full border-b border-gray-200 p-3 hover:bg-gray-50 items-center"):
                    # User info
                    with ui.column().classes("flex-1"):
                        ui.label(user["name"]).classes("font-medium text-sm")
                        ui.label(f"ID: {user['id']}").classes("text-xs text-gray-600 mt-1")
                    
                    # Email
                    with ui.element('div').classes("w-64"):
                        ui.label(user["email"]).classes("text-sm text-gray-600")
                    
                    # Timezone
                    with ui.element('div').classes("w-32 text-center"):
                        ui.label(user["user_timezone"]).classes("text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded")
                    
                    # Created date
                    with ui.element('div').classes("w-32 text-center"):
                        ui.label(user["created_at"]).classes("text-xs text-gray-500")
                    
                    # Actions
                    with ui.row().classes("w-32 justify-center gap-1"):
                        # Edit button
                        ui.button(
                            icon="edit",
                            on_click=lambda e,u=user: handle_edit_user(u["id"])
                        ).classes("text-blue-500 hover:bg-blue-50 p-1").props("flat dense size=sm").tooltip("Edit User")
                        
                        # Delete button
                        ui.button(
                            icon="delete",
                            on_click=lambda e,u=user: handle_delete_user(u["id"], u["name"])
                        ).classes("text-red-600 hover:bg-red-100 p-1").props("flat dense size=sm").tooltip("Delete User")

async def handle_search(search_text: str):
    """Handle search functionality"""
    refresh_user_data()

@ui.page("/user-management")
def user_management():
    """User management page"""
    global user_table
    
    # Check if user is logged in
    if not app.storage.user.get("session"):
        ui.navigate.to('/login')
        return
    
    ui.add_css('''
        .user-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .user-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
    ''')
    
    with ui.column().classes('user-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('👥 User Management').classes('text-3xl font-bold')
            
            # Actions and filters
            with ui.row().classes('items-center gap-3'):
                search_input = ui.input(
                    placeholder="Search users...",
                    on_change=lambda e: handle_search(e.value)
                ).classes('w-64')
                search_input.props('clearable outlined dense')
                
                ui.button(
                    icon="person_add",
                    text="New User",
                    on_click=handle_create_user
                ).classes("bg-blue-600 text-white hover:bg-blue-700").props("color=")
                
                ui.button(
                    icon="refresh",
                    on_click=refresh_user_data
                ).classes("p-2").tooltip("Refresh")
        
        # Main user table
        with ui.card().classes('user-card w-full'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Users').classes('text-xl font-semibold')
                    
                    # Info text
                    ui.label('Manage system users and their access').classes('text-sm text-gray-600')
                
                # User table container
                user_table = ui.column().classes("w-full")
    
    # Load initial data
    refresh_user_data()
    
    # Add layout
    layout()