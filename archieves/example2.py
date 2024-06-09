import logging
from dotenv import load_dotenv
import httpx
import os
import uuid
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ChatMessage
import json
import re
import csv
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize in-memory SQLite
memory = SqliteSaver.from_conn_string(":memory:")
# Set the base URL for the local LLM server
llama3_base_url = "http://192.168.86.51:8081/v1/chat/completions"

def data_to_csv(data):
    output = io.StringIO()
    csv_writer = csv.DictWriter(output, fieldnames=data.keys())
    csv_writer.writeheader()
    csv_writer.writerow(data)
    return output.getvalue().strip().replace("\n", ", ")

# Define the agent state
class AgentState(TypedDict):
    incident_type: str
    root_cause: str
    resolution: str
    incident_id: str
    data: dict
    content: List[str]
    revision_number: int
    max_revisions: int



# JSON configuration for multiple URLs
apps_config = json.loads("""
[
    {
        "app_id": "app1",
        "url": "http://dlyog02:8898/realtime",
        "INCIDENT_ANALYSIS_PROMPT": "You are an expert in smart grid monitoring. Determine the incident type (P0, P1, P2, P3, P4, or Normal) based on the provided real-time data.\\nHere are the thresholds for each incident type:\\n- P0-Emergency: Consumption_kWh > 500 kWh, Voltage_V < 170 V, Frequency_Hz < 44.0 Hz, PowerFactor < 0.50, ReactivePower_kVAR > 300 kVAR, Current_A > 3000 A, TransformerTemperature_C > 150 C\\n- P1-Fault: Consumption_kWh = 0 kWh, Voltage_V = 0 V, Frequency_Hz = 0.0 Hz, PowerFactor = 0.0, ReactivePower_kVAR = 0 kVAR, Current_A = 0 A, TransformerTemperature_C = 0 C\\n- P2-Severe: Consumption_kWh 400-500 kWh, Voltage_V 170-200 V, Frequency_Hz 44.0-48.5 Hz, PowerFactor 0.50-0.70, ReactivePower_kVAR 200-300 kVAR, Current_A 2000-3000 A, TransformerTemperature_C 120-150 C\\n- P3-Peak: Consumption_kWh 200-400 kWh, Voltage_V 220-230 V, Frequency_Hz 49.0-49.5 Hz, PowerFactor 0.80-0.85, ReactivePower_kVAR 100-200 kVAR, Current_A 1000-2000 A, TransformerTemperature_C 100-120 C\\n- P4-Low: Consumption_kWh 0-40 kWh, Voltage_V 200-230 V, Frequency_Hz 48.5-49.0 Hz, PowerFactor 0.70-0.80, ReactivePower_kVAR 0-50 kVAR, Current_A 0-500 A, TransformerTemperature_C 0-50 C\\n- Normal-Healthy: Consumption_kWh 40-200 kWh, Voltage_V 230-245 V, Frequency_Hz 49.5-50.5 Hz, PowerFactor 0.85-1.0, ReactivePower_kVAR 0-100 kVAR, Current_A 0-1000 A, TransformerTemperature_C 0-100 C",
        "ROOT_CAUSE_ANALYSIS_PROMPT": "You are an AI expert tasked with finding the root cause of an incident.\\nAnalyze the provided incident details and propose possible root causes and resolutions.\\nIncident Type: {incident_type}\\nData: {data}",
        "REFLECTION_PROMPT": "You are an expert reviewing an incident analysis.\\nGenerate critique and recommendations for improving the analysis and resolution.\\nIncident Type: {incident_type}\\nRoot Cause: {root_cause}\\nResolution: {resolution}",
        "email_address": "recipient@example.com"
    }
]
""")

def get_app_config(app_id):
    for app in apps_config:
        if app['app_id'] == app_id:
            return app
    return None

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
    #logger.info("Starting analysis_node")
    data = fetch_smart_grid_data(app_config['url'])
    if not data:
        incident_type = "P0"
        root_cause = "It seems the smart grid is down as no API response was received. Immediate attention is needed, and someone must check physically."
        new_state = state.copy()
        new_state.update({
            "incident_type": incident_type,
            "root_cause": root_cause,
            "resolution": root_cause,
            "data": root_cause,
            "incident_id": state.get("incident_id", str(uuid.uuid4()))
        })
        #logger.info(f"Updated state in analysis_node (no data): {new_state}")
        return new_state

    event_data = data_to_csv(data)  # Convert data to CSV string

    response = generate_response([
        {"role": "system", "content": app_config['INCIDENT_ANALYSIS_PROMPT']},
        {"role": "user", "content": json.dumps(data)}
    ])
    cleaned_response = clean_response(response)
    #logger.info(f"Generated response for incident analysis: {cleaned_response}")

    new_state = state.copy()
    new_state.update({
        "incident_type": cleaned_response,
        "data": data,
        "event_data": event_data,
        "incident_id": state.get("incident_id", str(uuid.uuid4()))
    })
    #logger.info(f"Updated state in analysis_node: {new_state}")
    return new_state

def root_cause_node(state: AgentState, app_config):
    logger.info("Starting root_cause_node")
    response = generate_response([
        {"role": "system", "content": app_config['ROOT_CAUSE_ANALYSIS_PROMPT'].format(incident_type=state['incident_type'], data=state['data'])},
        {"role": "user", "content": state['incident_type']}
    ])
    cleaned_response = clean_response(response)
    #logger.info(f"Generated response for root cause analysis: {cleaned_response}")

    new_state = state.copy()
    new_state['content'].append(cleaned_response)
    new_state.update({
        "root_cause": cleaned_response,
        "resolution": cleaned_response
    })
    #logger.info(f"Updated state in root_cause_node: {new_state}")
    return new_state

def reflection_node(state: AgentState, app_config):
    #logger.info("Starting reflection_node")
    response = generate_response([
        {"role": "system", "content": app_config['REFLECTION_PROMPT'].format(incident_type=state['incident_type'], root_cause=state['root_cause'], resolution=state['resolution'])},
        {"role": "user", "content": state['root_cause']}
    ])
    cleaned_response = clean_response(response)
    #logger.info(f"Generated response for reflection: {cleaned_response}")

    new_state = state.copy()
    new_state['content'].append(cleaned_response)
    new_state["revision_number"] += 1
    new_state.update({
        "critique": cleaned_response
    })
    #logger.info(f"Updated state in reflection_node: {new_state}")
    return new_state


def create_service_now_ticket(state: AgentState, app_config):
    new_state = state.copy()
    new_state['content'].append("ServiceNow ticket created successfully")
    new_state.update({
        "INC_NO": "TICKET123456"
    })
    print(f"ServiceNow Ticket - INC_NO: {new_state['INC_NO']}, INC_CATEGORY: {new_state['incident_type']}, INC_RCA: {new_state['root_cause']}")

    #logger.info(f"Updated state in create_service_now_ticket: {new_state}")
    return new_state

def send_email_notification(state: AgentState, app_config):
    new_state = state.copy()
    # Assume the email sending is successful
    new_state['content'].append("Email notification sent successfully")
    print("Email Node")
    #logger.info(f"Updated state in send_email_notification: {new_state}")
    return new_state


def should_continue(state):
    #logger.info(f"Checking if should continue: revision_number={state['revision_number']}, max_revisions={state['max_revisions']}")
    # If maximum revisions are reached, proceed to create the service now ticket
    if state["revision_number"] >= state["max_revisions"]:
        return "create_service_now_ticket"
    # Otherwise, continue with reflection
    return "reflect"

def run_agent_for_app(app_id):
    app_config = get_app_config(app_id)
    if not app_config:
        raise ValueError(f"No configuration found for app_id: {app_id}")

    builder = StateGraph(AgentState)

    builder.add_node("incident_analysis", lambda state: analysis_node(state, app_config))
    builder.add_node("root_cause_analysis", lambda state: root_cause_node(state, app_config))
    builder.add_node("reflect", lambda state: reflection_node(state, app_config))
    builder.add_node("create_service_now_ticket", lambda state: create_service_now_ticket(state, app_config))
    builder.add_node("send_email_notification", lambda state: send_email_notification(state, app_config))

    builder.set_entry_point("incident_analysis")

    # Add edges to ensure proper execution order
    builder.add_edge("incident_analysis", "root_cause_analysis")
    builder.add_conditional_edges(
        "root_cause_analysis", 
        should_continue, 
        {"create_service_now_ticket": "create_service_now_ticket", "reflect": "reflect"}
    )
    builder.add_edge("reflect", "root_cause_analysis")
    builder.add_edge("create_service_now_ticket", "send_email_notification")
    builder.add_edge("send_email_notification", END)

    graph = builder.compile(checkpointer=memory)

    # Save the graph to a file and display it
    graph_file_path = "smart_grid_graph.png"
    graph.get_graph().draw_png(graph_file_path)

    from IPython.display import Image

    # Display the graph image
    Image(graph_file_path)

    thread = {"configurable": {"thread_id": "1"}, "recursion_limit": 20}  # Temporarily increase recursion limit for debugging
    final_state = None

    for s in graph.stream({
        'incident_type': "",
        'root_cause': "",
        'resolution': "",
        'incident_id': str(uuid.uuid4()),
        'content': [],
        "max_revisions": 3,
        "revision_number": 0,
        "app_id": app_id  # Set the app_id here
    }, thread):
        final_state = s

    # With this logging check
    #logger.info(f"Final state: {final_state}")
    
    data = final_state

    final_state = data.get('send_email_notification', None)

    if final_state:
        final_output = {
            'INC_NO': final_state.get('incident_id', 'Missing incident_id'),
            'INC_TYPE': final_state.get('incident_type', 'Missing incident_type'),
            'INC_RCA': final_state.get('root_cause', 'Missing root_cause')
        }

        # Extract incident category from the incident type
        incident_type = final_output['INC_TYPE']
        incident_category = None
        for category in ["P4-Low", "P3-Peak", "P2-Severe", "P1-Fault", "P0-Emergency", "Normal-Healthy"]:
            if category in incident_type:
                incident_category = category
                break

        # Create the modified final output with the extracted incident category
        modified_final_output = {
            'INC_NO': final_output['INC_NO'],
            'INC_Event': final_output['INC_TYPE'],
            'INC_RCA': final_output['INC_RCA'],
            'INC_CATEGORY': incident_category
        }

        # Print or return the modified final output
        print(modified_final_output)
    else:
        final_output = {"error": "Final state is missing required information"}
        print(final_output)

# Trigger the agent flow for a specific app_id
run_agent_for_app("app1")
