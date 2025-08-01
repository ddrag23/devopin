from nicegui import ui, app
from ..layout import layout
from ...services.alarm_service import (
    get_pagination_alarms, 
    acknowledge_alarm, 
    resolve_alarm,
    get_alarm_summary,
    acknowledge_all_alarms,
    resolve_all_alarms
)
from ...utils.db_context import db_context
from fastapi.concurrency import run_in_threadpool
from datetime import datetime

# Global variables for UI elements
alarm_table = None
alarm_summary_container = None
current_page = 1
current_limit = 10
total_count = 0
pagination_info = None
page_label = None
prev_btn = None
next_btn = None

def get_severity_color(severity: str) -> str:
    """Get color based on alarm severity"""
    colors = {
        'critical': 'red',
        'high': 'amber', 
        'medium': 'amber',
        'low': '#3b82f6'  # Blue 500
    }
    return colors.get(severity.lower(), 'gray')

def get_severity_icon(severity: str) -> str:
    """Get icon based on alarm severity"""
    icons = {
        'critical': 'error',
        'high': 'warning',
        'medium': 'info',
        'low': 'check_circle'
    }
    return icons.get(severity.lower(), 'help')

def get_status_color(status: str) -> str:
    """Get color based on alarm status"""
    colors = {
        'active': 'red',
        'acknowledged': 'amber',
        'resolved': 'emerald'
    }
    return colors.get(status.lower(), 'gray')

async def handle_acknowledge_alarm(alarm_id: int):
    """Handle acknowledge alarm action"""
    try:
        result = await run_in_threadpool(_acknowledge_alarm_sync, alarm_id)
        if result:
            ui.notify("Alarm acknowledged successfully", type="positive")
            await refresh_alarm_data()
        else:
            ui.notify("Failed to acknowledge alarm", type="negative")
    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative")

async def handle_resolve_alarm(alarm_id: int):
    """Handle resolve alarm action"""
    try:
        result = await run_in_threadpool(_resolve_alarm_sync, alarm_id)
        if result:
            ui.notify("Alarm resolved successfully", type="positive")
            await refresh_alarm_data()
        else:
            ui.notify("Failed to resolve alarm", type="negative")
    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative")

def _acknowledge_alarm_sync(alarm_id: int):
    """Synchronous function to acknowledge alarm"""
    with db_context() as db:
        return acknowledge_alarm(db, alarm_id) is not None

def _resolve_alarm_sync(alarm_id: int):
    """Synchronous function to resolve alarm"""
    with db_context() as db:
        return resolve_alarm(db, alarm_id) is not None

async def handle_acknowledge_all():
    """Handle acknowledge all alarms action"""
    try:
        result = await run_in_threadpool(_acknowledge_all_sync)
        if result > 0:
            ui.notify(f"Successfully acknowledged {result} alarms", type="positive")
            await refresh_alarm_data()
        else:
            ui.notify("No active alarms to acknowledge", type="info")
    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative")

async def handle_resolve_all():
    """Handle resolve all alarms action"""
    try:
        result = await run_in_threadpool(_resolve_all_sync)
        if result > 0:
            ui.notify(f"Successfully resolved {result} alarms", type="positive")
            await refresh_alarm_data()
        else:
            ui.notify("No alarms to resolve", type="info")
    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative")

def _acknowledge_all_sync():
    """Synchronous function to acknowledge all alarms"""
    with db_context() as db:
        return acknowledge_all_alarms(db)

def _resolve_all_sync():
    """Synchronous function to resolve all alarms"""
    with db_context() as db:
        return resolve_all_alarms(db)

async def fetch_alarm_data(page: int = 1, limit: int = 10, search: str = ""):
    """Fetch alarm data with pagination"""
    # Create a mock request object with query parameters
    class MockRequest:
        def __init__(self, page: int, limit: int, search: str):
            self.query_params = {
                'page': str(page),
                'limit': str(limit),
                'search': search if search else ''
            }
    
    mock_request = MockRequest(page, limit, search)
    return await run_in_threadpool(_fetch_alarm_data_sync, mock_request)

def _fetch_alarm_data_sync(request):
    """Synchronous function to fetch alarm data"""
    # Get user session for timezone conversion
    user_session = app.storage.user.get("session")
    user_id = user_session.get('id') if user_session else None
    
    with db_context() as db:
        return get_pagination_alarms(request, db, user_id)

async def fetch_alarm_summary():
    """Fetch alarm summary statistics"""
    return await run_in_threadpool(_fetch_alarm_summary_sync)

def _fetch_alarm_summary_sync():
    """Synchronous function to fetch alarm summary"""
    with db_context() as db:
        return get_alarm_summary(db)

async def refresh_alarm_data():
    """Refresh alarm table and summary"""
    global current_page, current_limit, total_count
    
    # Fetch alarm data
    alarm_data = await fetch_alarm_data(current_page, current_limit)
    total_count = alarm_data.total
    
    # Update alarm table
    update_alarm_table(alarm_data.data)
    
    # Update pagination
    update_pagination_info()
    
    # Update summary
    summary_data = await fetch_alarm_summary()
    update_alarm_summary(summary_data)

def update_alarm_table(alarms):
    """Update the alarm table with new data"""
    global alarm_table
    
    if alarm_table:
        alarm_table.clear()
        
        if not alarms:
            with alarm_table:
                ui.label("No alarms found").classes("text-center text-gray-500 p-4")
            return
        
        with alarm_table:
            # Table header
            with ui.row().classes("w-full bg-gray-100 p-3 rounded-t-lg font-bold text-sm"):
                ui.label("Severity").classes("w-20 text-center")
                ui.label("Title").classes("flex-1")
                ui.label("Status").classes("w-24 text-center")
                ui.label("Source").classes("w-32")
                ui.label("Triggered").classes("w-32")
                ui.label("Actions").classes("w-32 text-center")
            
            # Table rows
            for alarm in alarms:
                with ui.row().classes("w-full border-b border-gray-200 p-3 hover:bg-gray-50 items-center"):
                    # Severity
                    with ui.element('div').classes("w-20 flex justify-center"):
                        ui.icon(get_severity_icon(alarm.severity)).classes(
                            f"text-{get_severity_color(alarm.severity)}-500"
                        ).tooltip(alarm.severity.title())
                    
                    # Title and Description
                    with ui.column().classes("flex-1"):
                        ui.label(alarm.title).classes("font-medium text-sm")
                        if alarm.description:
                            ui.label(alarm.description).classes("text-xs text-gray-600 mt-1")
                    
                    # Status
                    with ui.element('div').classes("w-24 flex justify-center"):
                        ui.chip(
                            alarm.status.title(),
                            color=get_status_color(alarm.status)
                        ).classes(f"text-xs {"text-white " if alarm.status != 'resolved' else "text-gray-500"}")
                    
                    # Source
                    with ui.column().classes("w-32"):
                        ui.label(alarm.source).classes("text-sm font-medium")
                        if alarm.source_id:
                            ui.label(alarm.source_id).classes("text-xs text-gray-600")
                    
                    # Triggered time
                    with ui.element('div').classes("w-32"):
                        triggered_time = alarm.triggered_at
                        if isinstance(triggered_time, str):
                            triggered_time = datetime.fromisoformat(triggered_time.replace('Z', '+00:00'))
                        ui.label(triggered_time.strftime('%d/%m %H:%M')).classes("text-xs")
                    
                    # Actions
                    with ui.row().classes("w-32 justify-center gap-1"):
                        if alarm.status == 'active':
                            ui.button(
                                icon="check",
                                on_click=lambda e,aid=alarm.id: handle_acknowledge_alarm(aid)
                            ).classes("text-amber-600 hover:bg-amber-100 p-1").props("flat dense size=sm").tooltip("Acknowledge")
                            
                            ui.button(
                                icon="done_all",
                                on_click=lambda e,aid=alarm.id: handle_resolve_alarm(aid)
                            ).classes("text-emerald-600 hover:bg-emerald-100 p-1").props("flat dense size=sm").tooltip("Resolve")
                        
                        elif alarm.status == 'acknowledged':
                            ui.button(
                                icon="done_all",
                                on_click=lambda e,aid=alarm.id: handle_resolve_alarm(aid)
                            ).classes("text-emerald-600 hover:bg-emerald-100 p-1").props("flat dense size=sm").tooltip("Resolve")
                        
                        else:  # resolved
                            ui.icon("check_circle").classes("text-emerald-500").tooltip("Resolved")

def update_pagination_info():
    """Update pagination information display"""
    global pagination_info, page_label, prev_btn, next_btn, current_page, total_count, current_limit
    
    if pagination_info:
        start_item = (current_page - 1) * current_limit + 1 if total_count > 0 else 0
        end_item = min(current_page * current_limit, total_count)
        pagination_info.text = f"Showing {start_item}-{end_item} of {total_count} alarms"
    
    if page_label:
        total_pages = max(1, (total_count + current_limit - 1) // current_limit)
        page_label.text = f"Page {current_page} of {total_pages}"
    
    # Update button states
    if prev_btn:
        if current_page <= 1:
            prev_btn.disable()
        else:
            prev_btn.enable()
    
    if next_btn:
        if current_page * current_limit >= total_count:
            next_btn.disable()
        else:
            next_btn.enable()

def update_alarm_summary(summary):
    """Update alarm summary cards"""
    global alarm_summary_container
    
    if alarm_summary_container:
        alarm_summary_container.clear()
        
        with alarm_summary_container:
            with ui.row().classes("w-full gap-4"):
                # Total alarms
                with ui.card().classes("flex-1 bg-blue-50 border-blue-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("notifications").classes("text-blue-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('total', 0))).classes("text-2xl font-bold text-blue-600")
                            ui.label("Total Alarms").classes("text-sm text-blue-500")
                
                # Active alarms
                with ui.card().classes("flex-1 bg-red-50 border-red-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("warning").classes("text-red-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('active', 0))).classes("text-2xl font-bold text-red-700")
                            ui.label("Active").classes("text-sm text-red-600")
                
                # Critical alarms
                with ui.card().classes("flex-1 bg-purple-50 border-purple-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("error").classes("text-purple-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('critical', 0))).classes("text-2xl font-bold text-purple-700")
                            ui.label("Critical").classes("text-sm text-purple-600")
                
                # Resolved alarms
                with ui.card().classes("flex-1 bg-emerald-50 border-emerald-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("check_circle").classes("text-emerald-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('resolved', 0))).classes("text-2xl font-bold text-emerald-700")
                            ui.label("Resolved").classes("text-sm text-emerald-600")

async def handle_pagination(direction: int):
    """Handle pagination navigation"""
    global current_page, total_count, current_limit
    
    if direction == -1 and current_page > 1:
        current_page -= 1
    elif direction == 1 and current_page * current_limit < total_count:
        current_page += 1
    
    await refresh_alarm_data()

async def handle_search(search_text: str):
    """Handle search functionality"""
    global current_page
    current_page = 1  # Reset to first page on search
    await refresh_alarm_data()

@ui.page("/alarm")
async def alarm_page():
    """Alarm management page"""
    global alarm_table, alarm_summary_container, current_page, current_limit, total_count, pagination_info, page_label, prev_btn, next_btn
    
    ui.add_css('''
        .alarm-container {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .alarm-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .summary-card {
            transition: transform 0.2s ease;
        }
        
        .summary-card:hover {
            transform: translateY(-2px);
        }
        
        .bulk-action-btn {
            transition: all 0.3s ease;
        }
        
        .bulk-action-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
    ''')
    
    with ui.column().classes('alarm-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('🚨 Alarm Management').classes('text-3xl font-bold')
            
            # Search and filters
            with ui.row().classes('items-center gap-3'):
                search_input = ui.input(
                    placeholder="Search alarms...",
                    on_change=lambda e: handle_search(e.value)
                ).classes('w-64')
                search_input.props('clearable outlined dense')
                
                ui.button(
                    icon="refresh",
                    on_click=refresh_alarm_data
                ).classes("p-2").tooltip("Refresh")
        
        # Summary cards
        alarm_summary_container = ui.row().classes("w-full gap-4 mb-6")
        
        # Bulk Actions
        with ui.card().classes('w-full mb-4'):
            with ui.row().classes('p-4 gap-3 items-center'):
                ui.label('Bulk Actions:').classes('text-lg font-semibold text-gray-700')
                
                ui.button(
                    "Acknowledge All Active",
                    icon="check",
                    on_click=handle_acknowledge_all
                ).classes("bulk-action-btn bg-amber-500 text-white hover:bg-amber-600")
                
                ui.button(
                    "Resolve All",
                    icon="done_all", 
                    on_click=handle_resolve_all
                ).classes("bulk-action-btn bg-emerald-500 text-white hover:bg-emerald-600")
                
                ui.label('Note: These actions affect all applicable alarms, not just those on current page.').classes('text-sm text-gray-500 ml-4')
        
        # Main alarm table
        with ui.card().classes('alarm-card w-full'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Alarm List').classes('text-xl font-semibold')
                
                # Alarm table container
                alarm_table = ui.column().classes("w-full")
                
                # Pagination info
                with ui.row().classes('w-full justify-between items-center mt-4'):
                    pagination_info = ui.label('Loading...').classes('text-sm text-gray-600')
                    
                    with ui.row().classes('gap-2'):
                        prev_btn = ui.button(
                            icon='chevron_left',
                            on_click=lambda: handle_pagination(-1)
                        ).classes('p-1').props('flat dense').tooltip('Previous Page')
                        
                        page_label = ui.label('Page 1').classes('text-sm px-2 py-1')
                        
                        next_btn = ui.button(
                            icon='chevron_right',
                            on_click=lambda: handle_pagination(1)
                        ).classes('p-1').props('flat dense').tooltip('Next Page')
    
    # Load initial data
    await refresh_alarm_data()
    
    # Add layout
    layout()