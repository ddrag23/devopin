from nicegui import ui
from ...services.project_service import get_project_by_id
from ...utils.db_context import db_context
from ..layout import layout
from ...services.project_log_service import get_pagination_log_project
from datetime import datetime, date

paginate = {'rowsPerPage': 10, 'sortBy': 'age', 'page': 1}

# Filter state
filters = {
    'search': '',
    'log_level': '',
    'date_from': '',
    'date_to': ''
}

@ui.refreshable
def table_paginate(project):
    columns = [
        {'name': 'message', 'label': 'Message', 'field': 'message', 'required': True, 'align': 'left'},
        {'name': 'log_level', 'label': 'Log Level', 'field': 'log_level','align': 'center'},
        {'name': 'log_time', 'label': 'Log Time', 'field': 'log_time','align': 'center'},
    ]
    
    log_table = ui.table(columns=columns, rows=[], row_key='name',pagination=paginate).classes('w-full').props('dense hover=hover')
    log_table.on("request",on_pagination_change)
    log_table.add_slot('no-data', r'''<div class="full-width row flex-center text-gray-500 q-gutter-sm">No logs available</div>''')
    log_table.add_slot("body-cell-log_time",""" <q-td :props="props">
                    {{ new Date(props.value).toLocaleString('en-GB', { 
                            year: 'numeric', 
                            month: '2-digit', 
                            day: '2-digit', 
                            hour: '2-digit', 
                            minute: '2-digit', 
                            second: '2-digit' 
                        }).replace(',', '') }}
            </q-td> """)
    
    # Load initial data
    refresh_table(project, log_table)

def refresh_table(project, log_table):
    with db_context() as db:
        # Build query params with filters
        query_params = {
            'page': str(paginate['page']),
            'limit': str(paginate['rowsPerPage']),
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
        
        result = get_pagination_log_project(
            db=db,
            request=None,
            query_params=query_params
        )
        log_table.rows = [log.model_dump() for log in result.data]
        log_table.pagination['rowsNumber'] = result.total
        log_table.update()

def on_pagination_change(e):
    paginate.update(e.args['pagination'])
    table_paginate.refresh()

def apply_filters():
    # Reset pagination to first page when applying filters
    paginate['page'] = 1
    table_paginate.refresh()

def reset_filters_with_inputs(search_input, log_level_select, date_from_input, date_to_input):
    # Reset all filters
    filters.update({
        'search': '',
        'log_level': '',
        'date_from': '',
        'date_to': ''
    })
    # Update UI elements
    search_input.value = ''
    log_level_select.value = ''
    date_from_input.value = ''
    date_to_input.value = ''
    
    paginate.update({'rowsPerPage': 10, 'sortBy': 'age', 'page': 1})
    table_paginate.refresh()

def reset_filters():
    # Reset all filters
    filters.update({
        'search': '',
        'log_level': '',
        'date_from': '',
        'date_to': ''
    })
    paginate.update({'rowsPerPage': 10, 'sortBy': 'age', 'page': 1})
    table_paginate.refresh()

@ui.page("/project/{id}/detail")
def detail(id: str):
    project = {}
    with db_context() as db:
        # Assuming you have a function to get project details by ID
        project = get_project_by_id(db, int(id))
        print(project)
        if project is None:
            ui.navigate.to("/404")
            return

        ui.label(f"Detail Project {project.name}").classes("text-2xl font-bold mb-6")
        
        with ui.card().classes("p-4 w-full"):
            with ui.tabs().classes('w-full').props('dense align=left') as tabs:
                one = ui.tab('Detail')
                two = ui.tab('Project Logs')
            with ui.tab_panels(tabs, value=two).classes('w-full'):
                with ui.tab_panel(one):
                    ui.label('Project details go here')
                    ui.label(f"Project ID: {project.id}")
                    ui.label(f"Project Name: {project.name}")
                    ui.label(f"Project Framework: {project.framework_type}")
                    ui.label(f"Project Description: {project.description}")
                    ui.label(f"Project Log Path: {project.log_path}")
                    ui.label(f"Project Alert Status: {'Enabled' if project.is_alert else 'Disabled'}")

                with ui.tab_panel(two):
                    # Header with filters and actions
                    with ui.row().classes('flex justify-between items-center mb-4 w-full'):
                        search_input = ui.input(
                                placeholder='Search...',
                                value=filters['search'],
                                on_change=lambda: apply_filters()
                            ).props('dense').classes('w-40')
                        search_input.bind_value_to(filters, 'search')
                        
                        # Filter controls in a compact row
                        with ui.row().classes('gap-2 items-center'):
                            
                            # Log level filter
                            log_level_select = ui.select(
                                options=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                                label='Level',
                            ).props('dense clearable').classes('w-32')
                            log_level_select.bind_value_to(filters, 'log_level')
                            
                            # Date from filter
                            date_from_input = ui.input(
                                placeholder='From',
                                value=filters['date_from']
                            ).props('dense type=date').classes('w-36')
                            date_from_input.bind_value_to(filters, 'date_from')
                            
                            # Date to filter
                            date_to_input = ui.input(
                                placeholder='To',
                                value=filters['date_to']
                            ).props('dense type=date').classes('w-36')
                            date_to_input.bind_value_to(filters, 'date_to')
                            
                            # Action buttons
                            ui.button(
                                '',
                                icon='filter_list',
                                on_click=apply_filters
                            ).props('color=primary dense').tooltip('Apply Filters')
                            
                            ui.button(
                                '',
                                icon='clear',
                                on_click=lambda: reset_filters_with_inputs(search_input, log_level_select, date_from_input, date_to_input)
                            ).props('color=secondary outline dense').tooltip('Reset Filters')
                            
                            ui.button(
                                '',
                                icon='refresh',
                                on_click=lambda: table_paginate.refresh()
                            ).props('color=primary outline dense').tooltip('Refresh')
                    
                    # Table
                    table_paginate(project)
                    
    layout()