from flask import Flask, render_template, jsonify, request
import threading
import time
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import actions

app = Flask(__name__)

# Initialize in-memory SQLite
memory = SqliteSaver.from_conn_string(":memory:")

# Define AgentState TypedDict (if not defined in actions.py)
class AgentState(TypedDict):
    equipment_id: str
    historical_data: str
    current_status: str
    data: dict
    analysis: dict
    prediction: str
    maintenance_plan: str
    priority: str
    ticket: str
    email: str
    teams: str
    reflection: str
    plan: str

# Define the graph structure
builder = StateGraph(AgentState)

builder.add_node("plan", actions.plan_node)
builder.add_node("monitor", actions.monitoring_node)
builder.add_node("analyze", actions.analysis_node)
builder.add_node("predict_failure", actions.prediction_node)
builder.add_node("plan_maintenance", actions.maintenance_plan_node)
builder.add_node("assess_priority", actions.priority_assessment_node)
builder.add_node("create_ticket", actions.create_ticket_node)
builder.add_node("email_notification", actions.email_notification_node)
builder.add_node("teams_notification", actions.teams_notification_node)
builder.add_node("self_reflect", actions.self_reflection_node)

builder.set_entry_point("plan")

builder.add_conditional_edges(
    "plan_maintenance", 
    actions.should_continue, 
    {END: END, "self_reflect": "self_reflect"}
)

builder.add_edge("plan", "monitor")
builder.add_edge("monitor", "analyze")
builder.add_edge("analyze", "predict_failure")
builder.add_edge("predict_failure", "plan_maintenance")
builder.add_edge("plan_maintenance", "assess_priority")
builder.add_edge("assess_priority", "create_ticket")
builder.add_edge("create_ticket", "email_notification")
builder.add_edge("email_notification", "teams_notification")
builder.add_edge("teams_notification", "self_reflect")
builder.add_edge("self_reflect", "monitor")

graph = builder.compile(checkpointer=memory)

@app.route('/trigger', methods=['POST'])
def trigger_agent():
    data = request.json
    thread_id = data.get('thread_id', "1")
    max_iterations = data.get('max_iterations', 2)
    revision_number = data.get('revision_number', 1)

    initial_state = {
        'equipment_id': "transformer_123",
        "historical_data": "temperature, voltage, current over the past 5 years",
        "current_status": "",
        "data": {},
        "analysis": {},
        "prediction": "",
        "maintenance_plan": "",
        "priority": "",
        "ticket": "",
        "email": "",
        "teams": "",
        "reflection": "",
        "plan": "",
    }
    
    def run_agent():
        for s in graph.stream(initial_state, {"configurable": {"thread_id": thread_id}, "recursion_limit": 10}):
            pass  # Process step result (you can log or handle it as needed)
        
        # Save the graph image
        graph_file_path = "static/real_time_maintenance_graph.png"
        graph.get_graph().draw_png(graph_file_path)
    
    agent_thread = threading.Thread(target=run_agent)
    agent_thread.start()

    return jsonify({"status": "Agent triggered", "thread_id": thread_id})

@app.route('/status/<thread_id>')
def get_status(thread_id):
    # For simplicity, assume agent finishes within a fixed time (simulate progress)
    time.sleep(5)  # Simulate waiting for agent completion
    return jsonify({
        "status": "completed",
        "result": {
            "plan": initial_state["plan"],
            "current_status": initial_state["current_status"],
            "analysis": initial_state["analysis"],
            "prediction": initial_state["prediction"],
            "maintenance_plan": initial_state["maintenance_plan"],
            "priority": initial_state["priority"],
            "ticket": initial_state["ticket"],
            "email": initial_state["email"],
            "teams": initial_state["teams"],
            "reflection": initial_state["reflection"]
        },
        "graph_image": "static/real_time_maintenance_graph.png"
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8899, debug=True, use_reloader=True)
