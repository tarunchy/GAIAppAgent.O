from flask import Flask, request, jsonify, render_template
from flask_apscheduler import APScheduler
from elasticsearch import Elasticsearch
from langgraph_workflow import create_workflow, execute_workflow
from config import *
import requests

app = Flask(__name__)

# Elasticsearch setup
es = Elasticsearch([ELASTICSEARCH_URL])

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        app_name = request.form['app_name']
        uptime_url = request.form['uptime_url']
        healthcheck_url = request.form['healthcheck_url']
        support_dl = request.form['support_dl']
        heartbeat_enabled = request.form.get('heartbeat_enabled') == 'on'
        healthcheck_enabled = request.form.get('healthcheck_enabled') == 'on'
        email_notification_enabled = request.form.get('email_notification_enabled') == 'on'
        teams_notification_enabled = request.form.get('teams_notification_enabled') == 'on'
        servicenow_ticket_enabled = request.form.get('servicenow_ticket_enabled') == 'on'

        doc = {
            'app_name': app_name,
            'uptime_url': uptime_url,
            'healthcheck_url': healthcheck_url,
            'support_dl': support_dl,
            'heartbeat_enabled': heartbeat_enabled,
            'healthcheck_enabled': healthcheck_enabled,
            'email_notification_enabled': email_notification_enabled,
            'teams_notification_enabled': teams_notification_enabled,
            'servicenow_ticket_enabled': servicenow_ticket_enabled
        }

        es.index(index='apps', body=doc)
        return jsonify({'message': 'Application registered successfully'})

    return render_template('register.html')

@app.route('/check_health', methods=['GET'])
def check_health():
    perform_health_checks()
    return jsonify({'message': 'Health check completed'})

def perform_health_checks():
    apps = es.search(index='apps', body={'query': {'match_all': {}}})['hits']['hits']
    for app in apps:
        app_data = app['_source']
        state = {"messages": [], "details": app_data, "plan": []}
        workflow = create_workflow()
        execute_workflow(workflow, state)

@scheduler.task('interval', id='do_health_checks', minutes=60, misfire_grace_time=900)
def scheduled_health_check():
    with app.app_context():
        perform_health_checks()

if __name__ == '__main__':
    app.run(debug=True)
