import uuid
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import time
from utils.config_loader import load_apps_config
from utils.agent_functions import (
    AgentState,
    analysis_node, root_cause_node, reflection_node, create_service_now_ticket,
    send_teams_notification, create_email_subject_body, send_email_notification,
    should_continue
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize in-memory SQLite
memory = SqliteSaver.from_conn_string(":memory:")

def run_agent_for_app(app_id):
    app_config = get_app_config(app_id)
    if not app_config:
        raise ValueError(f"No configuration found for app_id: {app_id}")

    builder = StateGraph(AgentState)

    builder.add_node("incident_data_capture", lambda state: analysis_node(state, app_config))
    builder.add_node("root_cause_analysis", lambda state: root_cause_node(state, app_config))
    builder.add_node("reflect", lambda state: reflection_node(state, app_config))
    builder.add_node("create_service_now_ticket", lambda state: create_service_now_ticket(state, app_config))
    builder.add_node("send_teams_notification", lambda state: send_teams_notification(state, app_config))
    builder.add_node("create_email_subject_body", lambda state: create_email_subject_body(state, app_config))
    builder.add_node("send_email_notification", lambda state: send_email_notification(state, app_config))

    builder.set_entry_point("incident_data_capture")

    builder.add_edge("incident_data_capture", "root_cause_analysis")
    builder.add_conditional_edges("root_cause_analysis", should_continue)
    builder.add_edge("reflect", "root_cause_analysis")
    builder.add_edge("create_service_now_ticket", "send_teams_notification")
    builder.add_edge("send_teams_notification", "create_email_subject_body")
    builder.add_edge("create_email_subject_body", "send_email_notification")
    builder.add_edge("send_email_notification", END)

    graph = builder.compile(checkpointer=memory)

    graph_file_path = "smart_grid_graph.png"
    graph.get_graph().draw_png(graph_file_path)

    thread = {"configurable": {"thread_id": "1"}, "recursion_limit": 20}
    final_state = None

    for s in graph.stream({
        'incident_type': "",
        'root_cause': "",
        'resolution': "",
        'incident_id': str(uuid.uuid4()),
        'content': [],
        "max_revisions": 3,
        "revision_number": 0,
        "app_id": app_id,
        "llm_response": "",
        "short_description": "",
        "incident_category": "",
        "INC_NO": "",
        "incident_url": "",
        "email_subject": "",
        "email_body": ""
    }, thread):
        final_state = s

        print(final_state)
    else:
        final_output = {"error": "Final state is missing required information"}
        print(final_state)

def continuous_monitoring():
    while True:
        apps_config = load_apps_config()
        active_apps = [app['app_id'] for app in apps_config if app['enabled'] == 'Yes']
        for app_id in active_apps:
            run_agent_for_app(app_id)
            time.sleep(1800)

def get_app_config(app_id):
    apps_config = load_apps_config()
    for app in apps_config:
        if app['app_id'] == app_id:
            return app
    return None
