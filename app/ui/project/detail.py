from nicegui import ui
from ...services.project_service import get_project_by_id
from ...utils.db_context import db_context
from ..layout import layout
from ...services.project_log_service import get_pagination_log_project
from datetime import datetime

# Global variables for UI elements
log_table = None
pagination_info = None
page_label = None
prev_btn = None
next_btn = None
current_page = 1
current_limit = 10
total_count = 0

# Filter state
filters = {
    'search': '',
    'log_level': '',
    'date_from': '',
    'date_to': ''
}

def get_log_level_color(level: str) -> str:
    """Get color based on log level"""
    colors = {
        'DEBUG': '#3b82f6',  # Blue 500
        'INFO': '#10b981',     # Emerald 500
        'WARNING': '#f59e0b',  # Amber 500
        'ERROR': '#ef4444',    # Red 500
        'CRITICAL': 'purple'
    }
    return colors.get(level.upper(), 'gray')

def get_log_level_icon(level: str) -> str:
    """Get icon based on log level"""
    icons = {
        'DEBUG': 'bug_report',
        'INFO': 'info',
        'WARNING': 'warning',
        'ERROR': 'error',
        'CRITICAL': 'dangerous'
    }
    return icons.get(level.upper(), 'help')

def refresh_log_data(project):
    """Refresh log table data"""
    global log_table, current_page, current_limit, total_count
    
    with db_context() as db:
        # Build query params with filters
        query_params = {
            'page': str(current_page),
            'limit': str(current_limit),
            'project_id__eq': str(project.id)
        }
        
        # Add search filter
        if filters['search']:
            query_params['search'] = filters['search']
        
        # Add log level filter
        if filters['log_level']:
            query_params['log_level__eq'] = filters['log_level']
        
        # Add date range filters
        if filters['date_from']:
            query_params['log_time__gte'] = filters['date_from']
        
        if filters['date_to']:
            # Add end of day to include the full day
            end_date = datetime.strptime(filters['date_to'], '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query_params['log_time__lte'] = end_date.isoformat()
        print(query_params)
        result = get_pagination_log_project(
            db=db,
            request=None,
            query_params=query_params
        )
        
        total_count = result.total
        update_log_table([log.model_dump() for log in result.data])
        update_pagination_info()

def update_log_table(logs):
    """Update the log table with new data"""
    global log_table
    
    if log_table:
        log_table.clear()
        
        if not logs:
            with log_table:
                ui.label("No logs found").classes("text-center text-gray-500 p-4")
            return
        
        with log_table:
            # Table header
            with ui.row().classes("w-full bg-gray-100 p-3 rounded-t-lg font-bold text-sm"):
                ui.label("Level").classes("w-24 text-center")
                ui.label("Message").classes("flex-1")
                ui.label("Time").classes("w-48 text-center")
            
            # Table rows
            for log in logs:
                with ui.row().classes("w-full border-b border-gray-200 p-3 hover:bg-gray-50 items-center"):
                    # Log Level
                    with ui.element('div').classes("w-24 flex justify-center"):
                        ui.icon(get_log_level_icon(log.get('log_level', ''))).classes(
                            f"text-{get_log_level_color(log.get('log_level', ''))}-500 mr-1"
                        )
                        ui.chip(
                            log.get('log_level', 'UNKNOWN'),
                            color=get_log_level_color(log.get('log_level', ''))
                        ).classes("text-xs")
                    
                    # Message
                    with ui.column().classes("flex-1"):
                        ui.label(log.get('message', '')).classes("text-sm")
                    
                    # Time
                    with ui.element('div').classes("w-48 text-center"):
                        log_time = log.get('log_time')
                        if log_time:
                            if isinstance(log_time, str):
                                try:
                                    log_time = datetime.fromisoformat(log_time.replace('Z', '+00:00'))
                                except (ValueError, TypeError):
                                    pass
                            if isinstance(log_time, datetime):
                                formatted_time = log_time.strftime('%d/%m/%Y %H:%M:%S')
                            else:
                                formatted_time = str(log_time)
                            ui.label(formatted_time).classes("text-xs font-mono")

def update_pagination_info():
    """Update pagination information display"""
    global pagination_info, page_label, prev_btn, next_btn, current_page, total_count, current_limit
    
    if pagination_info:
        start_item = (current_page - 1) * current_limit + 1
        end_item = min(current_page * current_limit, total_count)
        pagination_info.text = f"Showing {start_item}-{end_item} of {total_count} logs"
    
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

def apply_filters(project):
    """Apply filters and refresh data"""
    global current_page
    current_page = 1  # Reset to first page when applying filters
    refresh_log_data(project)

def reset_filters(project, search_input, log_level_select, date_from_input, date_to_input):
    """Reset all filters"""
    global current_page
    filters.update({
        'search': '',
        'log_level': '',
        'date_from': '',
        'date_to': ''
    })
    current_page = 1
    
    # Update UI elements
    search_input.value = ''
    log_level_select.value = ''
    date_from_input.value = ''
    date_to_input.value = ''
    
    refresh_log_data(project)

@ui.page("/project/{id}/detail")
def detail(id: str):
    """Project detail page"""
    global log_table, pagination_info, page_label, prev_btn, next_btn
    
    project = None
    with db_context() as db:
        project = get_project_by_id(db, int(id))
        if project is None:
            ui.navigate.to("/404")
            return
    
    ui.add_css('''
        .detail-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .detail-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .info-item {
            padding: 12px;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.02);
        }
    ''')
    
    with ui.column().classes('detail-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label(f'📁 {project.name} - Project Details').classes('text-3xl font-bold')
            
            # Back button
            ui.button(
                icon="arrow_back",
                text="Back to Projects", 
                on_click=lambda: ui.navigate.to("/project")
            ).classes("bg-gray-500 text-white")
        
        # Project Information Card
        with ui.card().classes('detail-card w-full mb-6'):
            with ui.column().classes('p-6 w-full'):
                ui.label('Project Information').classes('text-xl font-semibold mb-4')
                
                with ui.grid(columns=2).classes('w-full gap-4'):
                    # Project Name
                    with ui.column().classes('info-item'):
                        ui.label('Project Name').classes('text-sm font-medium text-gray-600')
                        ui.label(project.name).classes('text-lg font-semibold')
                    
                    # Framework
                    with ui.column().classes('info-item'):
                        ui.label('Framework').classes('text-sm font-medium text-gray-600')
                        ui.label(project.framework_type.title()).classes('text-lg font-semibold')
                    
                    # Log Path
                    with ui.column().classes('info-item'):
                        ui.label('Log Path').classes('text-sm font-medium text-gray-600')
                        ui.label(project.log_path).classes('text-lg font-mono')
                    
                    # Alert Status
                    with ui.column().classes('info-item'):
                        ui.label('Alert Status').classes('text-sm font-medium text-gray-600')
                        status_text = 'Enabled' if getattr(project, 'is_alert', False) else 'Disabled'
                        status_color = '#10b981' if getattr(project, 'is_alert', False) else 'gray'  # Emerald 500
                        ui.chip(status_text, color=status_color).classes('mt-1')
                
                # Description (full width if exists)
                if project.description:
                    ui.separator().classes('my-4')
                    with ui.column().classes('info-item w-full'):
                        ui.label('Description').classes('text-sm font-medium text-gray-600')
                        ui.label(project.description).classes('text-base')
        
        # Project Logs Card
        with ui.card().classes('detail-card w-full'):
            with ui.column().classes('p-6 w-full'):
                # Header with filters
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Project Logs').classes('text-xl font-semibold')
                    
                    # Filter controls
                    with ui.row().classes('items-center gap-2'):
                        search_input = ui.input(
                            placeholder='Search logs...',
                            value=filters['search'],
                        ).classes('w-48').props('outlined dense')
                        search_input.bind_value_to(filters,'search')
                        log_level_select = ui.select(
                            options=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                            label='Level',
                        ).classes('w-32').props('outlined dense clearable')
                        log_level_select.bind_value_to(filters,'log_level')
                        date_from_input = ui.input(
                            placeholder='From',
                            value=filters['date_from'],
                            on_change=lambda e: setattr(filters, 'date_from', e.value)
                        ).classes('w-36').props('outlined dense type=date')
                        date_from_input.bind_value_to(filters,'date_from')
                        
                        date_to_input = ui.input(
                            placeholder='To', 
                            value=filters['date_to'],
                            on_change=lambda e: setattr(filters, 'date_to', e.value)
                        ).classes('w-36').props('outlined dense type=date')
                        date_to_input.bind_value_to(filters,'date_to')
                        
                        # Action buttons
                        ui.button(
                            icon='filter_list',
                            on_click=lambda: apply_filters(project)
                        ).classes('p-2').props('color=primary').tooltip('Apply Filters')
                        
                        ui.button(
                            icon='clear',
                            on_click=lambda: reset_filters(project, search_input, log_level_select, date_from_input, date_to_input)
                        ).classes('p-2').props('color=secondary').tooltip('Reset Filters')
                        
                        ui.button(
                            icon='refresh',
                            on_click=lambda: refresh_log_data(project)
                        ).classes('p-2').props('color=primary outlined').tooltip('Refresh')
                
                # Log table container
                log_table = ui.column().classes("w-full")
                
                # Pagination info
                with ui.row().classes('w-full justify-between items-center mt-4'):
                    pagination_info = ui.label('Loading...').classes('text-sm text-gray-600')
                    
                    with ui.row().classes('gap-2'):
                        prev_btn = ui.button(
                            icon='chevron_left',
                            on_click=lambda: handle_pagination(-1, project)
                        ).classes('p-1').props('flat dense').tooltip('Previous Page')
                        
                        page_label = ui.label('Page 1').classes('text-sm px-2 py-1')
                        
                        next_btn = ui.button(
                            icon='chevron_right',
                            on_click=lambda: handle_pagination(1, project)
                        ).classes('p-1').props('flat dense').tooltip('Next Page')
    
    # Load initial data
    refresh_log_data(project)
    
    # Add layout
    layout()

def handle_pagination(direction: int, project):
    """Handle pagination navigation"""
    global current_page, total_count, current_limit
    
    if direction == -1 and current_page > 1:
        current_page -= 1
    elif direction == 1 and current_page * current_limit < total_count:
        current_page += 1
    
    refresh_log_data(project)