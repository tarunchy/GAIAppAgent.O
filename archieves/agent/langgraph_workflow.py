from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from typing import List, Literal, Annotated, TypedDict
import requests
from config import LLAMA3_API_URL

class HealthCheckState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    details: dict
    plan: list

# Define custom tools
@tool
def create_servicenow_ticket(issue: str, app_id: str, support_dl: str) -> str:
    # Placeholder for actual ServiceNow ticket creation logic
    print(f"Creating ServiceNow ticket for app {app_id}: {issue}")
    return f"ServiceNow ticket created for {app_id}: {issue}"

@tool
def send_email_notification(support_dl: str, subject: str, body: str) -> str:
    # Placeholder for actual email sending logic using SMTP
    print(f"Sending email to {support_dl} with subject '{subject}' and body '{body}'")
    return f"Email sent to {support_dl}"

@tool
def send_teams_notification(support_dl: str, message: str) -> str:
    # Placeholder for actual Teams notification logic
    print(f"Sending Teams notification to {support_dl} with message '{message}'")
    return f"Teams notification sent to {support_dl}"

@tool
def create_email_content(log_content: str) -> dict:
    response = requests.post(LLAMA3_API_URL, json={
        "messages": [
            {"role": "system", "content": "You are an assistant that creates email content."},
            {"role": "user", "content": f"Create an email title and body from the following log content:\n{log_content}"}
        ],
        "max_tokens": 200
    })
    content = response.json()['choices'][0]['message']['content'].split('\n', 1)
    subject = content[0]
    body = content[1] if len(content) > 1 else ""
    return {"subject": subject, "body": body}

# LangGraph functions
def gather_details(state: HealthCheckState):
    return {"messages": [HumanMessage(content="Performing health check...")]}

def check_uptime(state: HealthCheckState):
    details = state['details']
    response = requests.get(details['uptime_url'])
    if response.status_code == 200:
        return {"messages": [AIMessage(content="Uptime check passed.")]}
    else:
        return {"messages": [AIMessage(content="Uptime check failed.")], "plan": ["send_notification"]}

def check_health(state: HealthCheckState):
    details = state['details']
    response = requests.get(details['healthcheck_url'])
    if response.status_code == 200:
        data = response.json()
        log_content = data['messages']
        # Process log content using Llama3 API
        response = requests.post(LLAMA3_API_URL, json={
            "messages": [
                {"role": "system", "content": "You are an assistant that analyzes log content."},
                {"role": "user", "content": f"Analyze the following log content and identify any issues:\n{log_content}"}
            ],
            "max_tokens": 150
        })
        analysis = response.json()['choices'][0]['message']['content']
        if "issue" in analysis.lower():
            return {"messages": [AIMessage(content="Issues detected in logs.")], "plan": ["create_email_content", "send_notification"]}
        return {"messages": [AIMessage(content="Health check passed. No issues detected.")]}

def send_notification(state: HealthCheckState):
    details = state['details']
    email_content = state['email_content']
    support_dl = details['support_dl']
    app_id = details['app_id']
    issue = "Detected issues in health check."
    if details.get('email_notification_enabled', False):
        # Send email notification
        send_email_notification(support_dl, email_content['subject'], email_content['body'])
    if details.get('teams_notification_enabled', False):
        # Send Teams notification
        send_teams_notification(support_dl, f"{email_content['subject']}\n\n{email_content['body']}")
    if details.get('servicenow_ticket_enabled', False):
        # Create ServiceNow ticket
        create_servicenow_ticket(issue, app_id, support_dl)
    return {"messages": [AIMessage(content="Notification sent.")]}

def create_plan(state: HealthCheckState):
    details = state['details']
    plan = []
    if details.get('heartbeat_enabled', False):
        plan.append("check_uptime")
    if details.get('healthcheck_enabled', False):
        plan.append("check_health")
    return {"plan": plan, "messages": [AIMessage(content="Created dynamic plan based on registration details.")]}

def execute_step(state: HealthCheckState):
    if state['plan']:
        next_step = state['plan'].pop(0)
        return {"next_step": next_step}

def router(state: HealthCheckState) -> Literal["execute_step", "__end__"]:
    if state['plan']:
        return "execute_step"
    return "__end__"

def create_workflow():
    workflow = StateGraph(HealthCheckState)
    workflow.add_node("gather_details", gather_details)
    workflow.add_node("create_plan", create_plan)
    workflow.add_node("execute_step", execute_step)
    workflow.add_node("check_uptime", check_uptime)
    workflow.add_node("check_health", check_health)
    workflow.add_node("create_email_content", ToolNode([create_email_content]))
    workflow.add_node("send_notification", send_notification)

    workflow.set_entry_point("gather_details")
    workflow.add_edge("gather_details", "create_plan")
    workflow.add_conditional_edges("execute_step", router)
    workflow.add_edge("check_uptime", "execute_step")
    workflow.add_edge("check_health", "execute_step")
    workflow.add_edge("create_email_content", "send_notification")
    workflow.add_edge("send_notification", END)

    return workflow

def execute_workflow(workflow, state):
    workflow.compile().invoke(state)
