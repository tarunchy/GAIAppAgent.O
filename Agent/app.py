import logging
import time
import queue
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from threading import Thread
from utils.config_loader import load_apps_config, save_apps_config
from utils.state_graph import run_agent_for_app, continuous_monitoring
from ws.state_graph_ws import run_agent_for_app_ws  # Import the WS state graph
from ws.websocket_handler import start_websocket_server  # Import the websocket server function
import psutil
import os
import signal

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize queues and sets to track queued tasks
task_queue = queue.Queue()
queued_apps = set()

ws_task_queue = queue.Queue()
ws_queued_apps = set()

def worker():
    while True:
        app_id = task_queue.get()
        if app_id is None:
            break
        run_agent_for_app(app_id)
        task_queue.task_done()
        queued_apps.remove(app_id)

def ws_worker():
    while True:
        app_id = ws_task_queue.get()
        if app_id is None:
            break
        run_agent_for_app_ws(app_id)
        ws_task_queue.task_done()
        ws_queued_apps.remove(app_id)

# Start the worker threads
worker_thread = Thread(target=worker, daemon=True)
worker_thread.start()

ws_worker_thread = Thread(target=ws_worker, daemon=True)
ws_worker_thread.start()

@app.route('/')
def index():
    apps_config = load_apps_config()
    return render_template('websocket_ui.html', apps=apps_config)

@app.route('/edit/<app_id>', methods=['GET', 'POST'])
def edit_app(app_id):
    apps_config = load_apps_config()
    app_config = next((app for app in apps_config if app['app_id'] == app_id), None)
    if not app_config:
        return "App not found", 404

    if request.method == 'POST':
        data = request.get_json()
        app_config['url'] = data.get('url')
        app_config['INCIDENT_ANALYSIS_PROMPT'] = data.get('INCIDENT_ANALYSIS_PROMPT')
        app_config['ROOT_CAUSE_ANALYSIS_PROMPT'] = data.get('ROOT_CAUSE_ANALYSIS_PROMPT')
        app_config['REFLECTION_PROMPT'] = data.get('REFLECTION_PROMPT')
        app_config['email_address'] = data.get('email_address')
        app_config['teams_webhook_url'] = data.get('teams_webhook_url')
        app_config['awx_url'] = data.get('awx_url')
        app_config['P0'] = data.get('P0')
        app_config['enabled'] = data.get('enabled')
        app_config['description'] = data.get('description')

        save_apps_config(apps_config)
        return jsonify({'status': 'success'})

    return render_template('edit.html', app=app_config)

@app.route('/add', methods=['POST'])
def add_app():
    apps_config = load_apps_config()
    data = request.get_json()
    new_app = {
        'app_id': data.get('app_id'),
        'description': data.get('description'),
        'url': data.get('url', 'NA'),
        'INCIDENT_ANALYSIS_PROMPT': data.get('INCIDENT_ANALYSIS_PROMPT', 'NA'),
        'ROOT_CAUSE_ANALYSIS_PROMPT': data.get('ROOT_CAUSE_ANALYSIS_PROMPT', 'NA'),
        'REFLECTION_PROMPT': data.get('REFLECTION_PROMPT', 'NA'),
        'email_address': data.get('email_address', 'NA'),
        'teams_webhook_url': data.get('teams_webhook_url', 'NA'),
        'awx_url': data.get('awx_url', 'NA'),
        'P0': data.get('P0', 'NA'),
        'enabled': data.get('enabled', 'No')
    }
    apps_config.append(new_app)
    save_apps_config(apps_config)
    return jsonify({'status': 'success'})


@app.route('/active_apps')
def active_apps():
    apps_config = load_apps_config()
    active_apps = [app for app in apps_config if app['enabled'] == 'Yes']
    return render_template('active_apps.html', apps=active_apps)

@app.route('/run_agent/<app_id>', methods=['POST'])
def run_agent(app_id):
    if app_id in queued_apps:
        return jsonify({'status': f'Agent for {app_id} is already in queue'})
    
    queued_apps.add(app_id)
    task_queue.put(app_id)
    return jsonify({'status': f'Queued agent for {app_id}'})

@app.route('/run_agent_ws/<app_id>', methods=['POST'])
def run_agent_ws(app_id):
    if app_id in ws_queued_apps:
        return jsonify({'status': f'Agent for {app_id} is already in queue'})
    
    ws_queued_apps.add(app_id)
    ws_task_queue.put(app_id)
    return jsonify({'status': f'Queued agent for {app_id} with WebSocket support'})

@app.route('/websocket_ui')
def websocket_ui():
    apps_config = load_apps_config()
    return render_template('websocket_ui.html', apps=apps_config)

def kill_previous_instance(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    os.kill(proc.info['pid'], signal.SIGKILL)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            # Skip processes we don't have permission to access or that no longer exist
            continue

if __name__ == '__main__':
    kill_previous_instance(6789)

    monitor_thread = Thread(target=continuous_monitoring, daemon=True)
    monitor_thread.start()

    websocket_thread = Thread(target=start_websocket_server, daemon=True)
    websocket_thread.start()

    app.run(host='0.0.0.0', port=8899, debug=True, use_reloader=True)
