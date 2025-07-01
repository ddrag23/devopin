from nicegui import ui, app
from ..layout import layout
from ...utils.db_context import db_context
from ...services.user_service import get_user_by_id
from ...models.user import User
from ...utils.timezone_utils import get_available_timezones
from sqlalchemy.exc import IntegrityError


def update_user_timezone(user_id: int, new_timezone: str):
    """Update user timezone in database"""
    try:
        with db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.user_timezone = new_timezone
                db.commit()
                
                # Update session data
                user_session = app.storage.user.get("session", {})
                user_session['user_timezone'] = new_timezone
                app.storage.user['session'] = user_session
                
                ui.notify(f'Timezone updated to {new_timezone}', type='positive')
                return True
            else:
                ui.notify('User not found', type='negative')
                return False
    except Exception as e:
        ui.notify(f'Error updating timezone: {str(e)}', type='negative')
        return False


@ui.page('/settings')
def settings_page():
    layout()
    
    # Get current user from session
    user_session = app.storage.user.get("session")
    if not user_session:
        ui.navigate.to('/login')
        return
    
    user_id = user_session.get('id')
    current_timezone = 'UTC'
    
    # Get current user timezone from database
    try:
        with db_context() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if user and hasattr(user, 'user_timezone'):
                current_timezone = user.user_timezone
    except Exception:
        pass
    
    with ui.card().classes('w-full max-w-2xl mx-auto mt-8'):
        ui.label('Settings').classes('text-2xl font-bold mb-4')
        
        with ui.card().classes('w-full mb-4'):
            ui.label('Timezone Settings').classes('text-lg font-semibold mb-2')
            ui.label('Select your timezone to display log times correctly:').classes('text-gray-600 mb-4')
            
            # Current timezone display
            with ui.row().classes('items-center mb-4'):
                ui.label('Current timezone:').classes('font-medium')
                ui.chip(current_timezone, color='primary').classes('ml-2')
            
            # Timezone selector
            timezone_select = ui.select(
                options=get_available_timezones(),
                value=current_timezone,
                label='Select Timezone'
            ).classes('w-full mb-4')
            
            # Save button
            def save_timezone():
                new_timezone = timezone_select.value
                if update_user_timezone(user_id, new_timezone):
                    # Refresh the page to show updated timezone
                    ui.navigate.to('/settings', new_tab=False)
            
            ui.button('Save Timezone', on_click=save_timezone, color='primary')
        
        # Additional settings can be added here
        with ui.card().classes('w-full mb-4'):
            ui.label('Account Information').classes('text-lg font-semibold mb-2')
            
            with ui.row().classes('items-center mb-2'):
                ui.label('Name:').classes('font-medium w-20')
                ui.label(user_session.get('name', 'N/A')).classes('text-gray-700')
            
            with ui.row().classes('items-center mb-2'):
                ui.label('Email:').classes('font-medium w-20')
                ui.label(user_session.get('email', 'N/A')).classes('text-gray-700')