import logging
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from threading import Thread
from utils.config_loader import load_apps_config, save_apps_config
from utils.state_graph import run_agent_for_app, continuous_monitoring

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    apps_config = load_apps_config()
    return render_template('index.html', apps=apps_config)

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
        'url': '',
        'INCIDENT_ANALYSIS_PROMPT': '',
        'ROOT_CAUSE_ANALYSIS_PROMPT': '',
        'REFLECTION_PROMPT': '',
        'email_address': '',
        'teams_webhook_url': '',
        'P0': '',
        'enabled': 'No'
    }
    apps_config.append(new_app)
    save_apps_config(apps_config)
    return jsonify({'status': 'success'})

@app.route('/active_apps')
def active_apps():
    apps_config = load_apps_config()
    active_apps = [app for app in apps_config if app['enabled'] == 'Yes']
    return render_template('active_apps.html', apps=active_apps)

@app.route('/run_agent/<app_id>')
def run_agent(app_id):
    thread = Thread(target=run_agent_for_app, args=(app_id,))
    thread.start()
    return jsonify({'status': f'Started agent for {app_id}'})

if __name__ == '__main__':
    monitor_thread = Thread(target=continuous_monitoring, daemon=True)
    monitor_thread.start()
    app.run(host='0.0.0.0', port=8899, debug=True, use_reloader=True)
