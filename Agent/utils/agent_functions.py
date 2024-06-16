import base64
import httpx
import json
import re
import csv
import io
import logging
import configparser  # Import configparser
from typing import TypedDict, List  # Import TypedDict and List
import uuid
from utils.config_loader import load_config_ini

# Load secrets.ini
secrets_config = load_config_ini()
secrets_path = secrets_config['settings']['secrets_config_path']

# Load the secrets.ini file
def load_secrets_ini(path):
    config = configparser.ConfigParser()
    config.read(path)
    return config

secrets_config = load_secrets_ini(secrets_path)
secrets = secrets_config['secrets']

servicenow_instance = secrets['servicenow_instance']
servicenow_username = secrets['servicenow_username']
servicenow_password = secrets['servicenow_password']
llama3_base_url = secrets['llama3_base_url']
email_api_url = secrets['email_api_url']
awx_api_token = secrets['awx_api_token']

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    incident_type: str
    root_cause: str
    resolution: str
    incident_id: str
    data: str
    content: List[str]
    revision_number: int
    max_revisions: int
    llm_response: str
    short_description: str
    incident_category: str
    INC_NO: str
    incident_url: str
    email_subject: str
    email_body: str

def data_to_csv(data):
    output = io.StringIO()
    csv_writer = csv.DictWriter(output, fieldnames=data.keys())
    csv_writer.writeheader()
    csv_writer.writerow(data)
    content = output.getvalue().split("\n")
    single_line_csv = ", ".join(content)
    return single_line_csv.strip()

def fetch_smart_grid_data(url):
    try:
        response = httpx.get(url, timeout=60.0)
        response.raise_for_status()
        return response.json()
    except BaseException:
        return None

def generate_response(messages):
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "messages": messages,
        "max_gen_len": 150,
        "temperature": 0.1,
        "top_p": 0.9,
        "do_sample": True
    }

    try:
        response = httpx.post(llama3_base_url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise Exception("Request timed out")
    except httpx.RequestError as e:
        raise Exception(f"An error occurred while requesting {e.request.url!r}.")
    
    result = response.json()
    return result['choices'][0]['message']['content']

def clean_response(response):
    cleaned = re.sub(r'</?s>', '', response)
    return cleaned.strip()

def analysis_node(state: AgentState, app_config):
    logger.info("Starting analysis_node")
    data = fetch_smart_grid_data(app_config['url'])
    if not data:
        return {
            "llm_response": app_config['P0'],
            "short_description": app_config['P0'],
            "incident_category": 'P0-Outage',
            "data": app_config['P0']
            
        }

    response = generate_response([
        {"role": "system", "content": app_config['INCIDENT_ANALYSIS_PROMPT']},
        {"role": "user", "content": json.dumps(data)}
    ])
    llm_response = clean_response(response)
    
    incident_category = None
    for category in ["P4-Low", "P3-Peak", "P2-Severe", "P1-Fault", "P0-Emergency", "Normal-Healthy"]:
        if category in llm_response:
            incident_category = category
            break
    
    print(llm_response)

    return {
        "llm_response": llm_response,
        "short_description": llm_response,
        "incident_category": incident_category,
        "data": json.dumps(data)
    }

def root_cause_node(state: AgentState, app_config):
    logger.info(f"Starting root_cause_node: {state}")
    response = generate_response([
        {"role": "system", "content": app_config['ROOT_CAUSE_ANALYSIS_PROMPT']},
        {"role": "user", "content": state['llm_response']}
    ])
    llm_response = clean_response(response)

    return {
        "incident_category": state['incident_category'],
        "short_description": state['short_description'],
        "llm_response": llm_response,
        "revision_number": state["revision_number"],
        "cyber_secuirty_incident": 'No'
    }

def reflection_node(state: AgentState, app_config):
    logger.info(f"Starting reflection_node: {state}")
    response = generate_response([
        {"role": "system", "content": app_config['REFLECTION_PROMPT']},
        {"role": "user", "content": state['llm_response']}
    ])
    llm_response = clean_response(response)

    return {
        "incident_category": state['incident_category'],
        "short_description": state['short_description'],
        "llm_response": llm_response,
        "revision_number": state["revision_number"] + 1
    }

def create_service_now_ticket(state: AgentState, app_config):
    logger.info(f"Starting create_service_now_ticket: {state}")

    def encode_credentials(username, password):
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return encoded_credentials

    incident_impact_urgency = {
        "P0-Emergency": ("1", "1"),
        "P1-Fault": ("2", "2"),
        "P2-Severe": ("3", "3"),
        "P3-Peak": ("4", "4"),
        "P4-Low": ("5", "5"),
    }

    impact, urgency = incident_impact_urgency.get(state['incident_category'], ("3", "3"))

    url = f"{servicenow_instance}/api/now/table/incident"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {encode_credentials(servicenow_username, servicenow_password)}"
    }
    data = {
        "short_description": state['short_description'],
        "impact": impact,
        "urgency": urgency,
        "category": "incident",
        "description": state['short_description'],
        "work_notes": state['llm_response']
    }
    response = httpx.post(url, headers=headers, json=data)
    if response.status_code == 201:
        incident_sys_id = response.json()["result"]["sys_id"]
        incident_url = f"{servicenow_instance}/nav_to.do?uri=incident.do?sys_id={incident_sys_id}"
        logger.info(f"Incident created successfully: {incident_sys_id}")

        return {
            "INC_NO": incident_sys_id,
            "incident_category": state['incident_category'],
            "short_description": state['short_description'],
            "llm_response": state['llm_response'],
            "incident_url": incident_url
        }
    else:
        logger.error(f"Failed to create incident. Status code: {response.status_code}")
        return state

def send_teams_notification(state: AgentState, app_config):
    logger.info(f"Starting send_teams_notification: {state}")

    incident_url = state["incident_url"]
    logger.info(f"incident_url in send_teams_notification: {incident_url}")

    incident_impact_urgency = {
        "P0-Emergency": ("1", "1"),
        "P1-Fault": ("2", "2"),
        "P2-Severe": ("3", "3"),
        "P3-Peak": ("4", "4"),
        "P4-Low": ("5", "5"),
    }

    impact, urgency = incident_impact_urgency.get(state['incident_category'], ("3", "3"))

    message = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": "ServiceNow Incident Created",
        "sections": [{
            "activityTitle": "New ServiceNow Incident Created",
            "activitySubtitle": f"Priority: {state['incident_type']}, Impact: {impact}, Urgency: {urgency}",
            "activityImage": "https://www.servicenow.com/etc.clientlibs/servicenow/clientlibs/clientlib-base/resources/images/brand/logo-full-color.svg",
            "facts": [
                {"name": "Incident Category", "value": state['incident_category']},
                {"name": "Description", "value": state['short_description']},
                {"name": "Root Cause Analysis", "value": state['llm_response']},
                {"name": "Incident URL", "value": state['incident_url']}
            ],
            "markdown": True
        }]
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = httpx.post(app_config['teams_webhook_url'], headers=headers, json=message, timeout=180)
    if response.status_code == 200:
        logger.info("Notification sent to Microsoft Teams successfully")

        content = state.get('content', []).copy()
        content.append("Teams notification sent successfully")

        return {
            "INC_NO": state['INC_NO'],
            "incident_category": state['incident_category'],
            "short_description": state['short_description'],
            "llm_response": state['llm_response'],
            "incident_url": state['incident_url']
        }
    else:
        logger.error(f"Failed to send notification to Microsoft Teams. Status code: {response.status_code}")
        return {
            "INC_NO": state['INC_NO'],
            "incident_category": state['incident_category'],
            "short_description": state['short_description'],
            "llm_response": state['llm_response'],
            "incident_url": state['incident_url']
        }

def create_email_subject_body(state: AgentState, app_config):
    logger.info(f"Starting create_email_subject_body: {state}")
    email_prompt = f"""
    You are an AI tasked with creating an email based on the following information:
    Short Description: {state['short_description']}
    Root Cause: {state['llm_response']}
    
    Please provide a JSON with two attributes: "email_subject" and "email_body".
    """

    response = generate_response([
        {"role": "system", "content": "Generate an email subject and body based on the input provided."},
        {"role": "user", "content": email_prompt}
    ])
    email_content = clean_response(response)
    email_json = json.loads(email_content)

    return {
        "INC_NO": state['INC_NO'],
        "incident_category": state['incident_category'],
        "short_description": state['short_description'],
        "llm_response": state['llm_response'],
        "incident_url": state['incident_url'],
        "email_subject": email_json.get("email_subject", "Default Subject"),
        "email_body": email_json.get("email_body", "Default Body")
    }

def send_email_notification(state: AgentState, app_config):
    logger.info(f"Starting send_email_notification: {state}")
    recipient_email = app_config["email_address"]
    incident_url = state.get("incident_url", "N/A")
    logger.info(f"incident_url in send_email_notification: {incident_url}")
    email_data = {
        "recipient_email": recipient_email,
        "subject": f"New ServiceNow Incident Created - ID: {state['INC_NO']}, Priority: {state['incident_category']}, Subject: {state['email_subject']}",
        "body": f"{state['email_body']} An incident has been created in ServiceNow.\n\nIncident ID: {state['INC_NO']}\nPriority: {state['incident_category']}\n\nYou can view the incident here: {state['incident_url']}"
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = httpx.post(email_api_url, headers=headers, json=email_data)
    if response.status_code == 200:
        logger.info("Email sent successfully")
        new_state = state.copy()
        new_state['content'].append("Email notification sent successfully")
        logger.info(f"Updated state in send_email_notification: {new_state}")
        return {
            "INC_NO": state['INC_NO'],
            "incident_category": state['incident_category'],
            "short_description": state['short_description'],
            "llm_response": state['llm_response'],
            "incident_url": state['incident_url']
        }
    else:
        logger.error(f"Failed to send email. Status code: {response.status_code}")
        return {
            "INC_NO": state['INC_NO'],
            "incident_category": state['incident_category'],
            "short_description": state['short_description'],
            "llm_response": state['llm_response'],
            "incident_url": state['incident_url']
        }

def should_continue(state):
    logger.info(f"Checking if should continue: revision_number={state['revision_number']}, max_revisions={state['max_revisions']}")
    if state["revision_number"] >= state["max_revisions"]:
        if state["cyber_secuirty_incident"] == "No":
            return "create_service_now_ticket"
        else:
            return "act_on_cyber_secuirty_breach"
    return "reflect"

def find_next_node(state):
    logger.info(f"Checking iIncident Category={state['incident_category']}")
    if state["incident_category"] == 'P0-Outage':
        return "self_heal_app"
    return "root_cause_analysis"

def trigger_awx_job(state, app_config,app_action):
    try:
        # Extract details from config
        awx_url = app_config['awx_url'] 
        # Hardcode the app_action as "start"
        
        
        # Headers
        headers = {
            "Authorization": f"Bearer {awx_api_token}",
            "Content-Type": "application/json"
        }
        
        # Payload
        payload = {
            "extra_vars": {
                "app_action": app_action
            }
        }
        
        # Make the request
        response = httpx.post(awx_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Check the response
        if response.status_code == 201:
            
            return {
                "incident_category": state['incident_category'],
                "short_description": state['short_description'],
                "llm_response": "App outage Observed. Self-Healing launched successfully with AWX. App should be up soon. However please do an RCA"
            }
        else:
            logger.error(f"Failed to launch job. Status code: {response.status_code}, Response: {response.text}")
           
            return {
                "incident_category": state['incident_category'],
                "short_description": state['short_description'],
                "llm_response": "App outage Observed. Self-Healing Failed with AWX"
            }

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {
            "incident_category": state.get('incident_category', 'unknown'),
            "short_description": state.get('short_description', 'unknown'),
            "llm_response": "App outage Observed. Self-Healing Failed with AWX"
        }