# ws/state_graph_ws.py
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
    should_continue,trigger_awx_job, find_next_node
)
from ws.websocket_handler import node_wrapper  # Import the wrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize in-memory SQLite
memory = SqliteSaver.from_conn_string(":memory:")

def run_agent_for_app_ws(app_id):
    app_config = get_app_config(app_id)
    if not app_config:
        raise ValueError(f"No configuration found for app_id: {app_id}")

    builder = StateGraph(AgentState)

    builder.add_node("incident_data_capture", lambda state: node_wrapper(analysis_node, "incident_data_capture", state, app_config))
    builder.add_node("self_heal_app", lambda state: node_wrapper(trigger_awx_job, "trigger_awx_job", state, app_config,"start"))
    builder.add_node("root_cause_analysis", lambda state: node_wrapper(root_cause_node, "root_cause_analysis", state, app_config))
    builder.add_node("reflect", lambda state: node_wrapper(reflection_node, "reflect", state, app_config))
    builder.add_node("act_on_cyber_secuirty_breach", lambda state: node_wrapper(trigger_awx_job, "trigger_awx_job", state, app_config,"stop"))
    builder.add_node("create_service_now_ticket", lambda state: node_wrapper(create_service_now_ticket, "create_service_now_ticket", state, app_config))
    builder.add_node("send_teams_notification", lambda state: node_wrapper(send_teams_notification, "send_teams_notification", state, app_config))
    builder.add_node("create_email_subject_body", lambda state: node_wrapper(create_email_subject_body, "create_email_subject_body", state, app_config))
    builder.add_node("send_email_notification", lambda state: node_wrapper(send_email_notification, "send_email_notification", state, app_config))

    builder.set_entry_point("incident_data_capture")

    
    builder.add_conditional_edges("incident_data_capture", find_next_node, {"self_heal_app":"self_heal_app","root_cause_analysis":"root_cause_analysis"})
    builder.add_conditional_edges("root_cause_analysis", should_continue, {"act_on_cyber_secuirty_breach":"act_on_cyber_secuirty_breach","root_cause_analysis":"root_cause_analysis","reflect": "reflect" })
    builder.add_edge("reflect", "root_cause_analysis")
    builder.add_edge("self_heal_app", "create_service_now_ticket")
    builder.add_edge("act_on_cyber_secuirty_breach", "create_service_now_ticket")
    builder.add_edge("create_service_now_ticket", "send_teams_notification")
    builder.add_edge("send_teams_notification", "create_email_subject_body")
    builder.add_edge("create_email_subject_body", "send_email_notification")
    builder.add_edge("send_email_notification", END)

    graph = builder.compile(checkpointer=memory)
    # Save the graph to a file and display it
    graph_file_path = f"static/images/{app_id}_smart_grid_graph.png"
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
        final_state = {"error": "Final state is missing required information"}
        print(final_state)

def get_app_config(app_id):
    apps_config = load_apps_config()
    for app in apps_config:
        if app['app_id'] == app_id:
            return app
    return None
