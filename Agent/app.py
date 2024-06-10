import logging
import time
from flask import Flask, render_template, request, redirect, url_for
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
        app_config['url'] = request.form['url']
        app_config['INCIDENT_ANALYSIS_PROMPT'] = request.form['INCIDENT_ANALYSIS_PROMPT']
        app_config['ROOT_CAUSE_ANALYSIS_PROMPT'] = request.form['ROOT_CAUSE_ANALYSIS_PROMPT']
        app_config['REFLECTION_PROMPT'] = request.form['REFLECTION_PROMPT']
        app_config['email_address'] = request.form['email_address']
        app_config['teams_webhook_url'] = request.form['teams_webhook_url']
        app_config['P0'] = request.form['P0']
        app_config['enabled'] = request.form['enabled']
        app_config['description'] = request.form['description']

        save_apps_config(apps_config)
        return redirect(url_for('index'))

    return render_template('edit.html', app=app_config)

@app.route('/active_apps')
def active_apps():
    apps_config = load_apps_config()
    active_apps = [app for app in apps_config]
    return render_template('active_apps.html', apps=active_apps)

@app.route('/run_agent/<app_id>')
def run_agent(app_id):
    thread = Thread(target=run_agent_for_app, args=(app_id,))
    thread.start()
    return f"Started agent for {app_id}", 200

if __name__ == '__main__':
    monitor_thread = Thread(target=continuous_monitoring, daemon=True)
    monitor_thread.start()
    app.run(host='0.0.0.0', port=8899, debug=True, use_reloader=True)



