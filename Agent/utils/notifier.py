import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_teams_notification(state, app_config):
    logger.info(f"Starting send_teams_notification: {state}")

    incident_url = state["incident_url"]
    logger.info(f"incident_url in send_teams_notification: {incident_url}")
    message = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": "ServiceNow Incident Created",
        "sections": [{
            "activityTitle": "New ServiceNow Incident Created",
            "activitySubtitle": f"Priority: {state['incident_type']}, Impact: 3, Urgency: 3",
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
    response = httpx.post(app_config['teams_webhook_url'], headers=headers, json=message)
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
        return state

def send_email_notification(state, app_config):
    logger.info(f"Starting send_email_notification: {state}")
    email_api_url = "http://dlyog02:8900/send_email"
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
        return state
