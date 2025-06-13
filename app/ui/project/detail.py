from nicegui import ui
from ...services.project_service import get_project_by_id
from ...utils.db_context import db_context
from ..layout import layout
from ...services.project_log_service import get_pagination_log_project

class PaginationState:
    def __init__(self):
        self.page = 1
        self.limit = 10

pagination = PaginationState()
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
                    columns = [
                        {'name': 'message', 'label': 'Message', 'field': 'message', 'required': True, 'align': 'left'},
                        {'name': 'log_level', 'label': 'Log Level', 'field': 'log_level','align': 'center'},
                        {'name': 'log_time', 'label': 'Log Time', 'field': 'log_time','align': 'center'},
                    ]
                    log_table = ui.table(columns=columns, rows=[], row_key='name').classes('w-full').props('dense hover=hover')
                    log_table.add_slot('no-data', r'''<div class="full-width row flex-center text-gray-500 q-gutter-sm">No logs available</div>''')
                    def on_pagination_change(e):
                        pagination.page = e.args['page']
                        pagination.limit = e.args['rowsPerPage']
                        refresh_table()

                    log_table.on('pagination', on_pagination_change)

                    # 👇 Refresh function
                    def refresh_table():
                        with db_context() as db:
                            result = get_pagination_log_project(
                                db=db,
                                request=None,
                                query_params={
                                    'page': str(pagination.page),
                                    'limit': str(pagination.limit),
                                    'project_id__eq': project.id  # pastikan ini sesuai field filter ProjectLogModel
                                }
                            )
                            log_table.rows = [log.model_dump() for log in result.data]
                            log_table.pagination['rowsNumber'] = result.total
                            log_table.update()

                    # 👇 Load initial data
                    refresh_table()
    layout()
