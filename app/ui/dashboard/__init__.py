from nicegui import ui
from ..layout import layout
from datetime import datetime
from ...services.system_metric_service import get_dashboard_system_metric
from ...utils.db_context import db_context
from fastapi.concurrency import run_in_threadpool
import json


def format_bytes(bytes_val):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"

def get_status_color(percentage):
    """Get color based on usage percentage"""
    if percentage < 50:
        return 'green'
    elif percentage < 80:
        return 'orange'
    else:
        return 'red'
        
def get_status_class(percentage):
    """Get CSS class based on usage percentage"""
    if percentage < 50:
        return 'low'
    elif percentage < 80:
        return 'medium'
    else:
        return 'high'


@ui.page("/dashboard")
async def dashboard():
    ui.add_css('''
        .dashboard-container {
            min-height: 100vh;
            padding: 20px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 20px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2) !important;
        }
        
        .metric-title {
            font-weight: 600 !important;
            font-size: 1.2em !important;
            margin-bottom: 10px !important;
        }
        
        .metric-value {
            font-size: 2.5em !important;
            font-weight: 700 !important;
        }
        
        .metric-subtitle {
            color: rgba(255, 255, 255, 0.7) !important;
            font-size: 0.9em !important;
        }
        
        .disk-item {
            background: rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 15px !important;
            margin: 8px 0 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        .disk-name {
            font-weight: 600 !important;
            margin-bottom: 5px !important;
        }
        
        .disk-stats {
            font-size: 0.85em !important;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .custom-progress {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        
        .cpu-fill.low { background: linear-gradient(90deg, #10b981, #059669); }
        .cpu-fill.medium { background: linear-gradient(90deg, #f59e0b, #d97706); }
        .cpu-fill.high { background: linear-gradient(90deg, #ef4444, #dc2626); }
        
        .memory-fill.low { background: linear-gradient(90deg, #10b981, #059669); }
        .memory-fill.medium { background: linear-gradient(90deg, #f59e0b, #d97706); }
        .memory-fill.high { background: linear-gradient(90deg, #ef4444, #dc2626); }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .timestamp-card {
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 12px !important;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(20px);
            border-radius: 20px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
    ''')
    
    # Global variables for UI elements
    global cpu_progress, memory_progress, cpu_label, memory_label, memory_available_label
    global disk_container, timestamp_label, performance_chart
    
    with ui.column().classes('dashboard-container w-full'):
        # Header with timestamp
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('🖥️ System Metrics Dashboard').classes('text-2xl font-bold')
            
            with ui.card().classes('timestamp-card'):
                with ui.row().classes('items-center'):
                    ui.html('<div class="status-indicator" style="background: #10b981;"></div>')
                    timestamp_label = ui.label('Loading...').classes('text-sm')
        
        with ui.row().classes('w-full gap-6'):
            # CPU Card
            with ui.card().classes('metric-card w-full md:flex-1'):
                with ui.column().classes('p-4 w-full'):
                    with ui.row().classes('items-center mb-4'):
                        ui.label('🔥').classes('text-3xl mr-3')
                        ui.label('CPU Usage').classes('metric-title')
                    
                    cpu_label = ui.label('0%').classes('metric-value')
                    cpu_progress = ui.linear_progress(value=0, color='red').classes('mt-2')
                    ui.label('Processor Load').classes('metric-subtitle mt-2')
            
            # Memory Card
            with ui.card().classes('metric-card w-full md:flex-1'):
                with ui.column().classes('p-4 w-full'):
                    with ui.row().classes('items-center mb-4'):
                        ui.label('💾').classes('text-3xl mr-3')
                        ui.label('Memory Usage').classes('metric-title')
                    
                    memory_label = ui.label('0%').classes('metric-value')
                    memory_progress = ui.linear_progress(value=0, color='teal').classes('mt-2')
                    memory_available_label = ui.label('Available: 0 GB').classes('metric-subtitle mt-2')
        
        # Disk usage and Performance chart
        with ui.row().classes('w-full gap-6 mt-6'):
            # Disk Usage Card
            with ui.card().classes('metric-card flex-1'):
                with ui.column().classes('p-4 w-full'):
                    with ui.row().classes('items-center mb-4'):
                        ui.label('💿').classes('text-3xl mr-3')
                        ui.label('Disk Usage').classes('metric-title')
                    
                    disk_container = ui.grid(columns=2).classes('w-full')
            
            # Performance Chart
            with ui.card().classes('metric-card chart-container flex-1'):
                with ui.column().classes('p-4 w-full'):
                    with ui.row().classes('items-center mb-4'):
                        ui.label('📊').classes('text-3xl mr-3')
                        ui.label('Performance Overview').classes('metric-title')

                    chart_data = {
                        'chart': {'type': 'line'},
                        'title': {'text': 'Performance Overview'},
                        'xAxis': {'categories': []},
                        'yAxis': {'title': {'text': 'Usage (%)'}},
                        'series': [
                            {'name': 'CPU', 'data': []},
                            {'name': 'Memory', 'data': []},
                        ],
                        'responsive': {'rules': []},
                    }

                    performance_chart = ui.highchart(chart_data).classes('h-64')
    
    # Update dashboard data
    await update_dashboard()
    
    # Schedule periodic updates every 5 seconds
    ui.timer(5.0, update_dashboard)
    layout()


async def update_dashboard():
    """Update dashboard with real metrics from database"""
    try:
        # Fetch real data from database
        system_metrics = await fetch_system_metrics()
        
        # Check if we have data
        if not system_metrics.get('last'):
            timestamp_label.text = "No data available"
            cpu_label.text = "0%"
            memory_label.text = "0%"
            memory_available_label.text = "Available: 0 GB"
            return
        
        last_metric = system_metrics['last']
        
        # Update timestamp
        timestamp_raw = last_metric.timestamp_log
        if isinstance(timestamp_raw, str):
            timestamp = datetime.fromisoformat(timestamp_raw.replace('Z', '+00:00'))
        else:
            timestamp = timestamp_raw

        timestamp_label.text = f"Last updated: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}"
        
        # Update CPU
        cpu_percent = float(last_metric.cpu_percent or 0)
        cpu_label.text = f"{cpu_percent:.1f}%"
        cpu_progress.value = round(cpu_percent/100, 2)
        cpu_progress.props(f'color={get_status_color(cpu_percent)}')
        
        # Update Memory
        memory_percent = float(last_metric.memory_percent or 0)
        memory_available = format_bytes(last_metric.memory_available or 0)
        memory_label.text = f"{memory_percent:.1f}%"
        memory_progress.value = round(memory_percent/100, 2)
        memory_available_label.text = f"Available: {memory_available}"
        
        # Update Disk Usage
        disk_container.clear()
        try:
            disk_usages = json.loads(last_metric.disk_usage or '{}')
            for path, disk_data in disk_usages.items():
                display_path = "Root" if path == "/" else path.split('/')[-1] or path
                
                with disk_container:
                    with ui.card().classes('disk-item w-full'):
                        with ui.column().classes('w-full'):
                            ui.label(display_path).classes('disk-name')
                            
                            with ui.row().classes('w-full justify-between'):
                                ui.label(f"Used: {format_bytes(disk_data.get('used', 0))}").classes('disk-stats')
                                ui.label(f"Free: {format_bytes(disk_data.get('free', 0))}").classes('disk-stats')
                            
                            # Create progress bar with appropriate color
                            disk_percent = disk_data.get('percent', 0)
                            disk_class = get_status_class(disk_percent)
                            ui.html(f'<div class="custom-progress"><div class="progress-fill memory-fill {disk_class}" style="width: {disk_percent}%"></div></div>').classes('mt-2')
        except (json.JSONDecodeError, AttributeError):
            with disk_container:
                ui.label("No disk data available").classes('text-sm text-gray-500')
        
        # Update Performance Chart with Real Historical Data
        history_data = system_metrics.get('history', [])
        
        if history_data and len(history_data) > 0:
            # Prepare data for chart (limit to last 30 points for performance)
            max_points = 30
            if len(history_data) > max_points:
                # Take evenly distributed samples
                step = len(history_data) // max_points
                sampled_data = history_data[::step][-max_points:]
            else:
                sampled_data = history_data[-max_points:]
            
            # Extract CPU and Memory data
            timestamps = []
            cpu_data = []
            memory_data = []
            
            for metric in sampled_data:
                # Format timestamp for chart
                timestamp = metric.timestamp_log
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                timestamps.append(timestamp.strftime('%d/%m %H:%M'))
                
                # Safe conversion with proper attribute access
                cpu_value = getattr(metric, 'cpu_percent', 0) or 0
                memory_value = getattr(metric, 'memory_percent', 0) or 0
                
                cpu_data.append(round(float(cpu_value), 1))
                memory_data.append(round(float(memory_value), 1))
            
            # Update chart with real data
            performance_chart.options['xAxis']['categories'] = timestamps
            performance_chart.options['series'][0]['data'] = cpu_data
            performance_chart.options['series'][1]['data'] = memory_data
            performance_chart.options['title']['text'] = f'Performance History (Current Month - {len(sampled_data)} points)'
            performance_chart.update()
        else:
            # No historical data available
            performance_chart.options['title']['text'] = 'Performance History (No Data Available)'
            performance_chart.options['xAxis']['categories'] = []
            performance_chart.options['series'][0]['data'] = []
            performance_chart.options['series'][1]['data'] = []
            performance_chart.update()
        
    except Exception as e:
        print(f"Error updating dashboard: {e}")
        timestamp_label.text = f"Error loading data: {str(e)}"
        cpu_label.text = "Error"
        memory_label.text = "Error"


async def fetch_system_metrics():
    """Fetch system metrics with current month history"""
    return await run_in_threadpool(_get_metrics_sync)


def _get_metrics_sync():
    """Synchronous function to get metrics with history"""
    with db_context() as db:
        return get_dashboard_system_metric(db)