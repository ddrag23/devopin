from nicegui import ui, app
from ..layout import layout
from ...services.threshold_service import (
    get_pagination_thresholds,
    create_threshold,
    update_threshold,
    delete_threshold,
    toggle_threshold,
    get_threshold_by_id,
    get_threshold_summary,
    duplicate_threshold
)
from ...schemas.threshold_schema import (
    ThresholdCreate,
    ThresholdUpdate,
    ThresholdToggle,
    ThresholdTypeEnum,
    ThresholdConditionEnum,
    ThresholdSeverityEnum
)
from ...utils.db_context import db_context
from fastapi.concurrency import run_in_threadpool
from datetime import datetime
from typing import Optional

# Global variables for UI elements
threshold_table = None
threshold_summary_container = None
current_page = 1
current_limit = 10
total_count = 0

def get_metric_icon(metric_type: str) -> str:
    """Get icon based on metric type"""
    icons = {
        'cpu': 'memory',
        'memory': 'storage',
        'disk': 'data_usage'
    }
    return icons.get(metric_type.lower(), 'settings')

def get_severity_color(severity: str) -> str:
    """Get color based on severity"""
    colors = {
        'critical': '#ef4444',  # Red 500
        'high': '#f59e0b',     # Amber 500
        'medium': '#f59e0b',   # Amber 500 (was yellow)
        'low': '#10b981'       # Emerald 500 (was blue)
    }
    return colors.get(severity.lower(), 'gray')

def get_condition_text(condition: str) -> str:
    """Get readable condition text"""
    conditions = {
        'greater_than': '>',
        'less_than': '<',
        'equals': '='
    }
    return conditions.get(condition.lower(), condition)

async def handle_create_threshold():
    """Show create threshold dialog"""
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Create New Alert Setting').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Name').classes('w-full mb-2').props('outlined')
        description_input = ui.textarea('Description').classes('w-full mb-2').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            metric_select = ui.select(
                {e.value: e.value.title() for e in ThresholdTypeEnum},
                label='Metric Type',
                value='cpu'
            ).classes('flex-1').props('outlined')
            
            condition_select = ui.select(
                {e.value: get_condition_text(e.value) for e in ThresholdConditionEnum},
                label='Condition',
                value='greater_than'
            ).classes('flex-1').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            threshold_input = ui.number(
                'Threshold (%)',
                min=0,
                max=100,
                step=0.1,
                value=85.0
            ).classes('flex-1').props('outlined')
            
            duration_input = ui.number(
                'Duration (min)',
                min=1,
                max=60,
                value=2
            ).classes('flex-1').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            severity_select = ui.select(
                {e.value: e.value.title() for e in ThresholdSeverityEnum},
                label='Severity',
                value='medium'
            ).classes('flex-1').props('outlined')
            
            cooldown_input = ui.number(
                'Cooldown (min)',
                min=0,
                max=120,
                value=5
            ).classes('flex-1').props('outlined')
        
        source_filter_input = ui.input('Source Filter (optional)').classes('w-full mb-4').props('outlined')
        enabled_switch = ui.switch('Enabled', value=True).classes('mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            async def create_action():
                from ...schemas.threshold_schema import ThresholdTypeEnum,ThresholdSeverityEnum,ThresholdConditionEnum
                try:
                    payload = ThresholdCreate(
                        name=name_input.value,
                        description=description_input.value or None,
                        metric_type=ThresholdTypeEnum(metric_select.value),
                        condition=ThresholdConditionEnum(condition_select.value),
                        threshold_value=float(threshold_input.value),
                        duration_minutes=int(duration_input.value),
                        severity=ThresholdSeverityEnum(severity_select.value),
                        cooldown_minutes=int(cooldown_input.value),
                        source_filter=source_filter_input.value or None,
                        is_enabled=enabled_switch.value
                    )
                    
                    result = await run_in_threadpool(_create_threshold_sync, payload)
                    if result:
                        ui.notify("Threshold created successfully", type="positive")
                        await refresh_threshold_data()
                        dialog.close()
                    else:
                        ui.notify("Failed to create threshold", type="negative")
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Create', on_click=create_action).props('color=primary')
    
    dialog.open()

async def handle_edit_threshold(threshold_id: int):
    """Show edit threshold dialog"""
    # Fetch current threshold data
    threshold_data = await run_in_threadpool(_get_threshold_by_id_sync, threshold_id)
    if not threshold_data:
        ui.notify("Threshold not found", type="negative")
        return
    
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Edit Alert Setting').classes('text-lg font-bold mb-4')
        
        name_input = ui.input('Name', value=threshold_data.name).classes('w-full mb-2').props('outlined')
        description_input = ui.textarea('Description', value=threshold_data.description or '').classes('w-full mb-2').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            metric_select = ui.select(
                {e.value: e.value.title() for e in ThresholdTypeEnum},
                label='Metric Type',
                value=threshold_data.metric_type
            ).classes('flex-1').props('outlined')
            
            condition_select = ui.select(
                {e.value: get_condition_text(e.value) for e in ThresholdConditionEnum},
                label='Condition',
                value=threshold_data.condition
            ).classes('flex-1').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            threshold_input = ui.number(
                'Threshold (%)',
                min=0,
                max=100,
                step=0.1,
                value=threshold_data.threshold_value
            ).classes('flex-1').props('outlined')
            
            duration_input = ui.number(
                'Duration (min)',
                min=1,
                max=60,
                value=threshold_data.duration_minutes
            ).classes('flex-1').props('outlined')
        
        with ui.row().classes('w-full gap-2 mb-2'):
            severity_select = ui.select(
                {e.value: e.value.title() for e in ThresholdSeverityEnum},
                label='Severity',
                value=threshold_data.severity
            ).classes('flex-1').props('outlined')
            
            cooldown_input = ui.number(
                'Cooldown (min)',
                min=0,
                max=120,
                value=threshold_data.cooldown_minutes
            ).classes('flex-1').props('outlined')
        
        source_filter_input = ui.input('Source Filter (optional)', value=threshold_data.source_filter or '').classes('w-full mb-4').props('outlined')
        enabled_switch = ui.switch('Enabled', value=threshold_data.is_enabled).classes('mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            async def update_action():
                try:
                    payload = ThresholdUpdate(
                        name=name_input.value,
                        description=description_input.value or None,
                        metric_type=metric_select.value,
                        condition=condition_select.value,
                        threshold_value=float(threshold_input.value),
                        duration_minutes=int(duration_input.value),
                        severity=severity_select.value,
                        cooldown_minutes=int(cooldown_input.value),
                        source_filter=source_filter_input.value or None,
                        is_enabled=enabled_switch.value
                    )
                    
                    result = await run_in_threadpool(_update_threshold_sync, threshold_id, payload)
                    if result:
                        ui.notify("Threshold updated successfully", type="positive")
                        await refresh_threshold_data()
                        dialog.close()
                    else:
                        ui.notify("Failed to update threshold", type="negative")
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Update', on_click=update_action).props('color=primary')
    
    dialog.open()

async def handle_toggle_threshold(threshold_id: int, current_status: bool):
    """Toggle threshold enabled/disabled status"""
    try:
        payload = ThresholdToggle(is_enabled=not current_status)
        result = await run_in_threadpool(_toggle_threshold_sync, threshold_id, payload)
        if result:
            status = "enabled" if not current_status else "disabled"
            ui.notify(f"Threshold {status} successfully", type="positive")
            await refresh_threshold_data()
        else:
            ui.notify("Failed to toggle threshold", type="negative")
    except Exception as e:
        ui.notify(f"Error: {str(e)}", type="negative")

async def handle_delete_threshold(threshold_id: int, threshold_name: str):
    """Show delete confirmation dialog"""
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Delete Threshold: {threshold_name}').classes('text-lg font-bold mb-4')
        ui.label('Are you sure you want to delete this threshold? This action cannot be undone.').classes('mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            async def delete_action():
                try:
                    result = await run_in_threadpool(_delete_threshold_sync, threshold_id)
                    if result:
                        ui.notify("Threshold deleted successfully", type="positive")
                        await refresh_threshold_data()
                        dialog.close()
                    else:
                        ui.notify("Failed to delete threshold", type="negative")
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Delete', on_click=delete_action).props('color=red')
    
    dialog.open()

async def handle_duplicate_threshold(threshold_id: int, threshold_name: str):
    """Show duplicate threshold dialog"""
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Duplicate Threshold: {threshold_name}').classes('text-lg font-bold mb-4')
        
        new_name_input = ui.input('New Name', value=f"{threshold_name} (Copy)").classes('w-full mb-4').props('outlined')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            async def duplicate_action():
                try:
                    result = await run_in_threadpool(_duplicate_threshold_sync, threshold_id, new_name_input.value)
                    if result:
                        ui.notify("Threshold duplicated successfully", type="positive")
                        await refresh_threshold_data()
                        dialog.close()
                    else:
                        ui.notify("Failed to duplicate threshold", type="negative")
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
            
            ui.button('Duplicate', on_click=duplicate_action).props('color=primary')
    
    dialog.open()

# Sync functions for database operations
def _create_threshold_sync(payload: ThresholdCreate):
    with db_context() as db:
        return create_threshold(db, payload)

def _update_threshold_sync(threshold_id: int, payload: ThresholdUpdate):
    with db_context() as db:
        return update_threshold(db, threshold_id, payload)

def _toggle_threshold_sync(threshold_id: int, payload: ThresholdToggle):
    with db_context() as db:
        return toggle_threshold(db, threshold_id, payload)

def _delete_threshold_sync(threshold_id: int):
    with db_context() as db:
        return delete_threshold(db, threshold_id)

def _get_threshold_by_id_sync(threshold_id: int):
    with db_context() as db:
        return get_threshold_by_id(db, threshold_id)

def _duplicate_threshold_sync(threshold_id: int, new_name: str):
    with db_context() as db:
        return duplicate_threshold(db, threshold_id, new_name)

async def fetch_threshold_data(page: int = 1, limit: int = 10, search: str = ""):
    """Fetch threshold data with pagination"""
    class MockRequest:
        def __init__(self, page: int, limit: int, search: str):
            self.query_params = {
                'page': str(page),
                'limit': str(limit),
                'search': search if search else ''
            }
    
    mock_request = MockRequest(page, limit, search)
    return await run_in_threadpool(_fetch_threshold_data_sync, mock_request)

def _fetch_threshold_data_sync(request):
    with db_context() as db:
        return get_pagination_thresholds(request, db)

async def fetch_threshold_summary():
    return await run_in_threadpool(_fetch_threshold_summary_sync)

def _fetch_threshold_summary_sync():
    with db_context() as db:
        return get_threshold_summary(db)

async def refresh_threshold_data():
    """Refresh threshold table and summary"""
    global current_page, current_limit, total_count
    
    threshold_data = await fetch_threshold_data(current_page, current_limit)
    total_count = threshold_data.total
    
    update_threshold_table(threshold_data.data)
    
    summary_data = await fetch_threshold_summary()
    update_threshold_summary(summary_data)

def update_threshold_table(thresholds):
    """Update the threshold table with new data"""
    global threshold_table
    
    if threshold_table:
        threshold_table.clear()
        
        if not thresholds:
            with threshold_table:
                ui.label("No thresholds found").classes("text-center text-gray-500 p-4")
            return
        
        with threshold_table:
            # Table header
            with ui.row().classes("w-full bg-gray-100 p-3 rounded-t-lg font-bold text-sm"):
                ui.label("Type").classes("w-20 text-center")
                ui.label("Name").classes("flex-1")
                ui.label("Condition").classes("w-32 text-center")
                ui.label("Severity").classes("w-24 text-center")
                ui.label("Duration").classes("w-24 text-center")
                ui.label("Status").classes("w-24 text-center")
                ui.label("Actions").classes("w-40 text-center")
            
            # Table rows
            for threshold in thresholds:
                with ui.row().classes("w-full border-b border-gray-200 p-3 hover:bg-gray-50 items-center"):
                    # Metric type
                    with ui.element('div').classes("w-20 flex justify-center"):
                        ui.icon(get_metric_icon(threshold.metric_type)).classes(
                            "text-blue-600"
                        ).tooltip(threshold.metric_type.title())
                    
                    # Name and Description
                    with ui.column().classes("flex-1"):
                        ui.label(threshold.name).classes("font-medium text-sm")
                        if threshold.description:
                            ui.label(threshold.description).classes("text-xs text-gray-600 mt-1")
                    
                    # Condition
                    with ui.element('div').classes("w-32 text-center"):
                        condition_text = f"{get_condition_text(threshold.condition)} {threshold.threshold_value}%"
                        ui.label(condition_text).classes("text-sm font-mono")
                    
                    # Severity
                    with ui.element('div').classes("w-24 flex justify-center"):
                        ui.chip(
                            threshold.severity.title(),
                            color=get_severity_color(threshold.severity)
                        ).classes("text-xs text-white")
                    
                    # Duration
                    with ui.element('div').classes("w-24 text-center"):
                        ui.label(f"{threshold.duration_minutes}m").classes("text-sm")
                    
                    # Status
                    with ui.element('div').classes("w-24 flex justify-center"):
                        status_color = "#10b981" if threshold.is_enabled else "#ef4444"
                        status_text = "Enabled" if threshold.is_enabled else "Disabled"
                        ui.chip(status_text, color=status_color).classes("text-xs text-white")
                    
                    # Actions
                    with ui.row().classes("w-40 justify-center gap-1"):
                        # Toggle button
                        toggle_icon = "toggle_off" if threshold.is_enabled else "toggle_on"
                        toggle_color_class = "red" if threshold.is_enabled else "emerald"
                        ui.button(
                            icon=toggle_icon,
                            on_click=lambda e, tid=threshold.id, status=threshold.is_enabled: handle_toggle_threshold(tid, status)
                        ).classes(f"text-{toggle_color_class}-600 hover:bg-{toggle_color_class}-100 p-1").props("flat dense size=sm").tooltip("Toggle")
                        
                        # Edit button
                        ui.button(
                            icon="edit",
                            on_click=lambda e, tid=threshold.id: handle_edit_threshold(tid)
                        ).classes("text-blue-500 hover:bg-blue-50 p-1").props("flat dense size=sm").tooltip("Edit")
                        
                        # Duplicate button
                        ui.button(
                            icon="content_copy",
                            on_click=lambda _, tid=threshold.id, name=threshold.name: handle_duplicate_threshold(tid, name)
                        ).classes("text-purple-600 hover:bg-purple-100 p-1").props("flat dense size=sm").tooltip("Duplicate")
                        
                        # Delete button
                        ui.button(
                            icon="delete",
                            on_click=lambda _, tid=threshold.id, name=threshold.name: handle_delete_threshold(tid, name)
                        ).classes("text-red-600 hover:bg-red-100 p-1").props("flat dense size=sm").tooltip("Delete")

def update_threshold_summary(summary):
    """Update threshold summary cards"""
    global threshold_summary_container
    
    if threshold_summary_container:
        threshold_summary_container.clear()
        
        with threshold_summary_container:
            with ui.row().classes("w-full gap-4"):
                # Total thresholds
                with ui.card().classes("flex-1 bg-blue-50 border-blue-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("settings").classes("text-blue-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('total', 0))).classes("text-2xl font-bold text-blue-600")
                            ui.label("Total Thresholds").classes("text-sm text-blue-500")
                
                # Enabled thresholds
                with ui.card().classes("flex-1 bg-emerald-50 border-emerald-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("toggle_on").classes("text-emerald-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('enabled', 0))).classes("text-2xl font-bold text-emerald-700")
                            ui.label("Enabled").classes("text-sm text-emerald-600")
                
                # CPU thresholds
                with ui.card().classes("flex-1 bg-purple-50 border-purple-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("memory").classes("text-purple-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('cpu', 0))).classes("text-2xl font-bold text-purple-700")
                            ui.label("CPU Thresholds").classes("text-sm text-purple-600")
                
                # Critical thresholds
                with ui.card().classes("flex-1 bg-red-50 border-red-200"):
                    with ui.row().classes("items-center p-4"):
                        ui.icon("error").classes("text-red-500 text-2xl mr-3")
                        with ui.column():
                            ui.label(str(summary.get('critical', 0))).classes("text-2xl font-bold text-red-700")
                            ui.label("Critical").classes("text-sm text-red-600")

async def handle_search(search_text: str):
    """Handle search functionality"""
    global current_page
    current_page = 1
    await refresh_threshold_data()

@ui.page("/threshold")
async def threshold_page():
    """Threshold management page"""
    global threshold_table, threshold_summary_container, current_page, current_limit, total_count
    
    ui.add_css('''
        .threshold-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .threshold-card {
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
    ''')
    
    with ui.column().classes('threshold-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('⚙️ Monitoring Settings').classes('text-3xl font-bold')
            
            # Actions and filters
            with ui.row().classes('items-center gap-3'):
                search_input = ui.input(
                    placeholder="Search thresholds...",
                    on_change=lambda e: handle_search(e.value)
                ).classes('w-64')
                search_input.props('clearable outlined dense')
                
                ui.button(
                    icon="add",
                    text="New Setting",
                    on_click=handle_create_threshold
                ).classes("bg-blue-600 text-white hover:bg-blue-700")
                
                ui.button(
                    icon="refresh",
                    on_click=refresh_threshold_data
                ).classes("p-2").tooltip("Refresh")
        
        # Summary cards
        threshold_summary_container = ui.row().classes("w-full gap-4 mb-6")
        
        # Main threshold table
        with ui.card().classes('threshold-card w-full'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Alert Settings').classes('text-xl font-semibold')
                    
                    # Info text
                    ui.label('Configure monitoring settings to automatically create alarms when conditions are met').classes('text-sm text-gray-600')
                
                # Threshold table container
                threshold_table = ui.column().classes("w-full")
    
    # Load initial data
    await refresh_threshold_data()
    
    # Add layout
    layout()