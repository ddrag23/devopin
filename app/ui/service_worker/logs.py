from nicegui import ui
from ..layout import layout
from ...utils.agent_controller import AgentController
import json
import threading
import time

# Global variables for log streaming
log_container = None
is_streaming = False
current_stream_id = None
log_thread = None
service_name_global = None

def stop_streaming():
    """Stop log streaming"""
    global is_streaming, current_stream_id, log_thread
    is_streaming = False
    
    if current_stream_id:
        try:
            agent_controller = AgentController()
            agent_controller.stop_log_stream(current_stream_id)
        except Exception as e:
            print(f"Error stopping stream: {e}")
    
    if log_thread and log_thread.is_alive():
        try:
            log_thread.join(timeout=1.0)
        except Exception:
            pass

def start_streaming():
    """Start log streaming"""
    global is_streaming, current_stream_id, log_thread, log_container, service_name_global
    
    if is_streaming:
        return
    
    if not service_name_global or service_name_global == "unknown":
        ui.notify("Service name not available", type="negative")
        return
    
    is_streaming = True
    
    def stream_logs():
        global current_stream_id, is_streaming
        try:
            agent_controller = AgentController()
            # Start stream - ensure service_name_global is not None
            if not service_name_global:
                ui.notify("Service name is not available", type="negative")
                return
            result = agent_controller.start_log_stream(service_name_global)
            
            if not result.get("success"):
                ui.notify(f"Failed to start log stream: {result.get('message', 'Unknown error')}", type="negative")
                return
            
            stream_socket = result.get("socket")
            if not stream_socket:
                ui.notify("No socket returned for streaming", type="negative")
                return
            
            # Read initial response to get stream_id
            try:
                response = stream_socket.recv(1024).decode()
                initial_data = json.loads(response)
                current_stream_id = initial_data.get("stream_id")
                
                if initial_data.get("success"):
                    ui.notify(f"Log streaming started for {service_name_global}", type="positive")
                
            except Exception as e:
                ui.notify(f"Error reading initial response: {e}", type="negative")
                return
            
            # Read log data continuously
            buffer = ""
            while is_streaming:
                try:
                    data = stream_socket.recv(1024).decode()
                    if not data:
                        break
                    
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                log_entry = json.loads(line)
                                command = log_entry.get("command")
                                
                                if command == "logs_data":
                                    # Parse journalctl JSON data
                                    log_data = log_entry.get("data", "")
                                    if log_data:
                                        try:
                                            journal_entry = json.loads(log_data)
                                            timestamp = journal_entry.get("__REALTIME_TIMESTAMP", "")
                                            message = journal_entry.get("MESSAGE", "")
                                            unit = journal_entry.get("_SYSTEMD_UNIT", service_name_global)
                                            
                                            # Format timestamp
                                            if timestamp:
                                                try:
                                                    ts = int(timestamp) / 1000000  # Convert from microseconds
                                                    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
                                                except Exception:
                                                    formatted_time = timestamp
                                            else:
                                                formatted_time = time.strftime("%Y-%m-%d %H:%M:%S")
                                            
                                            # Add log entry to UI
                                            if log_container:
                                                with log_container:
                                                    with ui.row().classes('w-full border-b border-gray-100 p-2 text-sm font-mono'):
                                                        ui.label(f"[{formatted_time}]").classes('text-gray-500 w-48 flex-shrink-0')
                                                        ui.label(f"{unit}:").classes('text-blue-600 w-32 flex-shrink-0')
                                                        ui.label(message).classes('flex-1 text-gray-800 break-words')
                                            
                                        except json.JSONDecodeError:
                                            # Handle non-JSON log data
                                            if log_container:
                                                with log_container:
                                                    with ui.row().classes('w-full border-b border-gray-100 p-2 text-sm font-mono'):
                                                        ui.label(f"[{time.strftime('%H:%M:%S')}]").classes('text-gray-500 w-48 flex-shrink-0')
                                                        ui.label(f"{service_name_global}:").classes('text-blue-600 w-32 flex-shrink-0')
                                                        ui.label(log_data).classes('flex-1 text-gray-800 break-words')
                                
                                elif command == "logs_stream_ended":
                                    ui.notify("Log streaming ended", type="info")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                except Exception as e:
                    if is_streaming:
                        print(f"Error reading log data: {e}")
                    break
            
            stream_socket.close()
            
        except Exception as e:
            ui.notify(f"Error in log streaming: {e}", type="negative")
        finally:
            is_streaming = False
    
    # Start streaming in background thread
    log_thread = threading.Thread(target=stream_logs, daemon=True)
    log_thread.start()

def clear_logs():
    """Clear log container"""
    global log_container
    if log_container:
        log_container.clear()
        with log_container:
            ui.label('Logs cleared. Click "Start Streaming" to view real-time logs...').classes('text-gray-500 text-center p-4')

@ui.page("/service-worker/logs")
def service_worker_logs(service: str = "unknown"):
    """Service worker logs viewing page"""
    global log_container, service_name_global
    
    # Get service name from URL parameters
    service_name_global = service
    
    ui.add_css('''
        .logs-container {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .logs-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        
        .log-entry {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
    ''')
    
    with ui.column().classes('logs-container w-full'):
        # Header
        with ui.row().classes('w-full justify-between items-center mb-6'):
            with ui.row().classes('items-center gap-3'):
                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/service-worker")
                ).classes("bg-gray-600 text-white hover:bg-gray-700").tooltip("Back to Service Workers")
                
                ui.label(f'📋 Service Logs: {service_name_global}').classes('text-3xl font-bold')
            
            # Control buttons
            with ui.row().classes('items-center gap-3'):
                ui.button(
                    'Start Streaming',
                    icon='play_arrow',
                    on_click=start_streaming
                ).classes('bg-green-600 text-white hover:bg-green-700')
                
                ui.button(
                    'Stop Streaming',
                    icon='stop',
                    on_click=stop_streaming
                ).classes('bg-red-600 text-white hover:bg-red-700')
                
                ui.button(
                    'Clear Logs',
                    icon='clear',
                    on_click=clear_logs
                ).classes('bg-amber-600 text-white hover:bg-amber-700')
        
        # Status indicator
        with ui.row().classes('w-full items-center gap-2 mb-4'):
            ui.icon('radio_button_unchecked').classes('text-red-500')
            ui.label('Stopped').classes('text-red-500 font-medium')
        
        # Main logs card
        with ui.card().classes('logs-card w-full'):
            with ui.column().classes('p-6 w-full'):
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Real-time Service Logs').classes('text-xl font-semibold')
                    
                    # Info text
                    ui.label(f'Streaming logs from journalctl -u {service_name_global} -f --output=json').classes('text-sm text-gray-600')
                
                # Log container with scroll area
                with ui.scroll_area().classes('w-full h-96 border border-gray-300 rounded bg-gray-50'):
                    log_container = ui.column().classes('w-full p-2')
                    
                    # Initial message
                    with log_container:
                        ui.label('Click "Start Streaming" to view real-time logs...').classes('text-gray-500 text-center p-4')
    
    # Auto-start streaming when page loads
    ui.timer(1.0, lambda: start_streaming(), once=True)
    
    # Cleanup when page is closed
    def cleanup():
        stop_streaming()
    
    ui.context.client.on_disconnect(cleanup)
    
    # Add layout
    layout()