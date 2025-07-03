from nicegui import ui, app
from ..layout import layout
from ...schemas.user_schema import UserUpdate, UserPasswordUpdate
from ...utils.db_context import db_context
from ...services.user_service import (
    get_user_by_id,
    update_user,
    update_user_password,
)
from datetime import datetime

# Available timezones
TIMEZONES = [
    'UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Phoenix',
    'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
    'Europe/Rome', 'Asia/Tokyo','Asia/Jakarta', 'Asia/Shanghai', 'Asia/Kolkata', 'Asia/Dubai',
    'Australia/Sydney', 'Pacific/Auckland'
]

def get_current_user():
    """Get current logged in user session"""
    return app.storage.user.get("session")

def update_session_data(updated_user):
    """Update session data with new user information"""
    session = app.storage.user.get("session")
    if session:
        session['name'] = updated_user.name
        session['email'] = updated_user.email
        app.storage.user['session'] = session

async def handle_update_profile(user_id: int, name_input, email_input, timezone_select):
    """Handle profile update"""
    try:
        if not name_input.value or not name_input.value.strip():
            ui.notify("Full name is required!", type="negative")
            return False
        
        if not email_input.value or not email_input.value.strip():
            ui.notify("Email address is required!", type="negative")
            return False
        
        with db_context() as db:
            payload = UserUpdate(
                name=name_input.value.strip(),
                email=email_input.value.strip().lower(),
                user_timezone=timezone_select.value
            )
            updated_user = update_user(db, user_id, payload)
            
            # Update session data
            update_session_data(updated_user)
            
            ui.notify("Profile updated successfully!", type="positive")
            return True
            
    except ValueError as e:
        ui.notify(f"Error: {str(e)}", type="negative")
        return False
    except Exception as e:
        ui.notify(f"Unexpected error: {str(e)}", type="negative")
        return False

async def handle_change_password(user_id: int, current_password_input, new_password_input, confirm_password_input):
    """Handle password change"""
    try:
        if not current_password_input.value:
            ui.notify("Current password is required!", type="negative")
            return False
        
        if not new_password_input.value or len(new_password_input.value) < 6:
            ui.notify("New password must be at least 6 characters!", type="negative")
            return False
        
        if new_password_input.value != confirm_password_input.value:
            ui.notify("New passwords do not match!", type="negative")
            return False
        
        with db_context() as db:
            payload = UserPasswordUpdate(
                current_password=current_password_input.value,
                new_password=new_password_input.value
            )
            update_user_password(db, user_id, payload)
            
            ui.notify("Password changed successfully!", type="positive")
            
            # Clear password fields
            current_password_input.value = ""
            new_password_input.value = ""
            confirm_password_input.value = ""
            
            return True
            
    except ValueError as e:
        ui.notify(f"Error: {str(e)}", type="negative")
        return False
    except Exception as e:
        ui.notify(f"Unexpected error: {str(e)}", type="negative")
        return False

@ui.page("/profile")
def profile_page():
    """User profile page"""
    
    # Check if user is logged in
    user_session = get_current_user()
    if not user_session:
        ui.navigate.to('/login')
        return
    
    user_id = user_session.get('id')
    if not user_id:
        ui.navigate.to('/login')
        return
    
    # Fetch current user data from database
    with db_context() as db:
        user_data = get_user_by_id(db, user_id)
    
    if not user_data:
        ui.notify("User data not found", type="negative")
        ui.navigate.to('/login')
        return
    
    ui.add_css('''
        .profile-container {
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .profile-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .section-divider {
            border-top: 1px solid #e2e8f0;
            margin: 24px 0;
        }
    ''')
    
    with ui.column().classes('profile-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('👤 My Profile').classes('text-3xl font-bold')
            
            # Account info badge
            with ui.row().classes('items-center gap-2'):
                ui.chip(f"ID: {user_data.id}", color='blue').classes('text-white')
                if user_data.created_at:
                    created_date = user_data.created_at.strftime('%Y-%m-%d')
                    ui.chip(f"Member since: {created_date}", color='green').classes('text-white')
        
        # Profile Information Card
        with ui.card().classes('profile-card w-full mb-6'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Profile Information').classes('text-xl font-semibold')
                    ui.icon('edit').classes('text-gray-400')
                
                # Profile form
                name_input = ui.input('Full Name', value=user_data.name).classes('w-full mb-4').props('outlined')
                email_input = ui.input('Email Address', value=user_data.email).classes('w-full mb-4').props('outlined')
                
                timezone_select = ui.select(
                    TIMEZONES,
                    label='Timezone',
                    value=user_data.user_timezone or 'UTC'
                ).classes('w-full mb-4').props('outlined')
                
                # Account details (read-only)
                with ui.row().classes('w-full gap-4 mb-4'):
                    with ui.column().classes('flex-1'):
                        ui.label('Account Created').classes('text-sm font-medium text-gray-600')
                        created_text = user_data.created_at.strftime('%Y-%m-%d %H:%M UTC') if user_data.created_at else 'N/A'
                        ui.label(created_text).classes('text-sm text-gray-800 bg-gray-100 p-2 rounded')
                    
                    with ui.column().classes('flex-1'):
                        ui.label('Last Updated').classes('text-sm font-medium text-gray-600')
                        updated_text = user_data.updated_at.strftime('%Y-%m-%d %H:%M UTC') if user_data.updated_at else 'N/A'
                        ui.label(updated_text).classes('text-sm text-gray-800 bg-gray-100 p-2 rounded')
                
                # Update button
                with ui.row().classes('w-full justify-end'):
                    ui.button(
                        'Update Profile',
                        icon='save',
                        on_click=lambda: handle_update_profile(user_id, name_input, email_input, timezone_select)
                    ).classes('bg-blue-600 text-white hover:bg-blue-700').props('color=primary')
        
        # Password Change Card
        with ui.card().classes('profile-card w-full'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Change Password').classes('text-xl font-semibold')
                    ui.icon('lock').classes('text-gray-400')
                
                ui.label('For security reasons, please enter your current password to change it.').classes('text-sm text-gray-600 mb-4')
                
                # Password form
                current_password_input = ui.input('Current Password', password=True).classes('w-full mb-4').props('outlined')
                
                with ui.row().classes('w-full gap-4 mb-4'):
                    new_password_input = ui.input('New Password', password=True).classes('flex-1').props('outlined')
                    confirm_password_input = ui.input('Confirm New Password', password=True).classes('flex-1').props('outlined')
                
                # Password requirements
                with ui.card().classes('w-full mb-4 bg-yellow-50 border border-yellow-200'):
                    with ui.column().classes('p-3'):
                        ui.label('Password Requirements:').classes('text-sm font-semibold text-yellow-800 mb-2')
                        ui.label('• Minimum 6 characters').classes('text-xs text-yellow-700')
                        ui.label('• Must match confirmation').classes('text-xs text-yellow-700')
                
                # Change password button
                with ui.row().classes('w-full justify-end'):
                    ui.button(
                        'Change Password',
                        icon='security',
                        on_click=lambda: handle_change_password(user_id, current_password_input, new_password_input, confirm_password_input)
                    ).classes('bg-red-600 text-white hover:bg-red-700').props('color=red')
        
        # Security Notice
        with ui.card().classes('w-full bg-blue-50 border border-blue-200'):
            with ui.column().classes('p-4'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('info', color='blue').classes('text-blue-600')
                    ui.label('Security Notice').classes('text-sm font-semibold text-blue-800')
                
                ui.label('Your account information is protected and encrypted. If you suspect any unauthorized access, please change your password immediately.').classes('text-xs text-blue-700')
    
    # Add layout
    layout()