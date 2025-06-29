from nicegui import ui, app
from .sidebar_menu import sidebar_menu
from ...utils.agent_controller import AgentController
from ...services.alarm_service import get_active_alarms
from ...utils.db_context import db_context
from fastapi.concurrency import run_in_threadpool

def check_agent_status():
    """Check agent status using AgentController - simple version"""
    # Try to communicate with agent
    result = AgentController.test_connection()
    
    if result.get("success"):
        return True, "Online"
    else:
        return False, "Offline"

async def get_alarm_count():
    """Get active alarm count"""
    try:
        return await run_in_threadpool(_get_alarm_count_sync)
    except Exception:
        return 0

def _get_alarm_count_sync():
    """Synchronous function to get alarm count"""
    with db_context() as db:
        active_alarms = get_active_alarms(db)
        return len(active_alarms)


def layout():
    user = app.storage.user.get("session")
    if not user:
        ui.navigate.to("/login")
        return
    current_path = ui.context.client.page.path
    
    # Check agent status
    agent_running, agent_status = check_agent_status()
    
    with (
        ui.header(elevated=True)
        .style("""
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    """)
        .classes("items-center justify-between px-6 py-3")
    ):
        # Left side: Menu button + Logo
        with ui.row().classes("items-center gap-4"):
            # Menu button dengan hover effect
            ui.button(icon="menu", on_click=lambda: left_drawer.toggle()).classes(
                "text-white hover:bg-white/20 transition-all duration-200 rounded-lg p-2"
            )

        # Logo/Brand dengan typography yang lebih baik
        with ui.row().classes("items-center gap-2"):
            ui.icon("code", size="lg").classes("text-white")
            ui.label("Devopin").classes("text-2xl font-bold text-white tracking-wide")

        # Right side: Alarm + User dropdown
        with ui.row().classes("items-center gap-3"):
            # Alarm Bell Icon with counter
            with ui.element('div').classes('relative'):
                alarm_button = ui.button(
                    icon="notifications",
                    on_click=lambda: ui.navigate.to("/alarm")
                ).classes(
                    "text-white hover:bg-white/20 transition-all duration-200 rounded-lg p-2"
                ).tooltip("View Alarms")
                
                # Alarm counter badge
                alarm_badge = ui.element('div').classes(
                    'absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-5 h-5 flex items-center justify-center px-1'
                ).style('display: none;')
                
                alarm_count_label = ui.label('0').classes('text-xs font-bold')
                alarm_count_label.move(alarm_badge)
            
            # User info
            ui.label(f"Welcome, {user.get('name', 'User')}").classes("text-white/80 text-sm hidden md:block")
            
            # Avatar placeholder with dropdown
            with ui.dropdown_button(
                icon="account_circle",
                auto_close=True,
            ).classes(
                "text-white bg-white/10 hover:bg-white/20 transition-all duration-200 rounded-lg px-4 py-2"
            ):
                ui.item(
                    "Profile",
                    on_click=lambda: ui.notify("Profile clicked", type="info"),
                )
                ui.item(
                    "Settings",
                    on_click=lambda: ui.notify("Settings clicked", type="info"),
                )
                ui.separator()
                ui.item(
                    "Logout",
                    on_click=lambda: (
                        app.storage.user.clear(),
                        ui.navigate.to("/login"),
                    ),
                ).classes("text-red-400")

    # Left drawer dengan design card-based
    with ui.left_drawer(bottom_corner=True, fixed=False).style("""
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
        border-right: 1px solid #e2e8f0;
    """) as left_drawer:
        
        # Agent status card in sidebar (simple)
        with ui.card().classes("m-2 p-3 bg-white/50 border border-gray-200 w-full"):
            with ui.row().classes("justify-between items-center gap-2 w-full"):
                # Status indicator
                with ui.row().classes("items-center gap-2"):
                    status_color = "green" if agent_running else "red"
                    ui.html(f'<div class="w-2 h-2 rounded-full bg-{status_color}-400 animate-pulse"></div>')
                    ui.label("Devopin Agent:").classes("text-sm font-medium")
                    with ui.element('div').classes(f"px-2 py-1 rounded-full text-xs font-medium {'bg-green-500 text-white' if agent_running else 'bg-red-500 text-white'}"):
                        ui.label(agent_status)
                # Quick refresh button
                ui.button(
                    icon="refresh", 
                    on_click=lambda: ui.navigate.reload()
                ).classes("text-white/60 hover:text-white/100 p-1").props("flat dense size=sm").tooltip("Refresh Agent Status")
                    
        
        # Navigation items dengan design simple
        with ui.column().classes("p-2 gap-1 w-full"):
            for item in sidebar_menu:
                is_active = current_path.startswith(item["path"])
                
                with ui.row().classes(
                    f"items-center gap-3 p-3 mx-2 rounded-lg w-full cursor-pointer transition-all duration-200 "
                    f"{'bg-gray-800 text-white shadow-md' if is_active else 'hover:bg-gray-100 text-gray-600'}"
                ):
                    ui.icon(item.get("icon", "home"), size="sm").classes(
                        "text-white" if is_active else "text-gray-600"
                    )
                    ui.link(
                        item.get("label", "Dashboard"), 
                        item.get("path", "/dashboard")
                    ).classes(
                        f"font-medium no-underline flex-1 "
                        f"{'text-white' if is_active else 'text-gray-600 hover:text-gray-800'}"
                    )
    
    # Update alarm counter periodically
    async def update_alarm_counter():
        try:
            count = await get_alarm_count()
            alarm_count_label.text = str(count)
            if count > 0:
                alarm_badge.style('display: flex;')
                # Add animation for new alarms
                alarm_button.classes(remove='animate-pulse')
                alarm_button.classes('animate-pulse')
            else:
                alarm_badge.style('display: none;')
                alarm_button.classes(remove='animate-pulse')
        except Exception as e:
            print(f"Error updating alarm counter: {e}")
    
    # Initial update and periodic updates
    ui.timer(10.0, update_alarm_counter)  # Update every 10 seconds
    
    # Run initial update
    ui.context.client.on_connect(update_alarm_counter)