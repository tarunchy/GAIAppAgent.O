import httpx
import json

llama3_base_url = "http://192.168.86.51:8081/v1/chat/completions"

def load_prompt(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

# Load prompts
PLAN_PROMPT = load_prompt('prompts/1_plan_prompt.txt')
MONITORING_PROMPT = load_prompt('prompts/2_monitoring_prompt.txt')
ANALYSIS_PROMPT = load_prompt('prompts/3_analysis_prompt.txt')
PREDICTION_PROMPT = load_prompt('prompts/4_prediction_prompt.txt')
MAINTENANCE_PLAN_PROMPT = load_prompt('prompts/5_maintenance_plan_prompt.txt')
PRIORITY_ASSESSMENT_PROMPT = load_prompt('prompts/6_priority_assessment_prompt.txt')
CREATE_TICKET_PROMPT = load_prompt('prompts/7_create_ticket_prompt.txt')
EMAIL_NOTIFICATION_PROMPT = load_prompt('prompts/8_email_notification_prompt.txt')
TEAMS_NOTIFICATION_PROMPT = load_prompt('prompts/9_teams_notification_prompt.txt')
SELF_REFLECTION_PROMPT = load_prompt('prompts/10_self_reflection_prompt.txt')

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

def plan_node(state):
    response = generate_response([
        {"role": "system", "content": PLAN_PROMPT},
        {"role": "user", "content": state['historical_data']}
    ])
    return {"plan": response}

def monitoring_node(state):
    try:
        response = httpx.get("http://dlyog02:8898/realtime")
        response.raise_for_status()
        data = response.json()
        log_entry = f"Consumption: {data['Consumption_kWh']} kWh, Voltage: {data['Voltage_V']} V, Frequency: {data['Frequency_Hz']} Hz"
        state['current_status'] = log_entry
    except httpx.RequestError as e:
        raise Exception(f"An error occurred while requesting {e.request.url!r}.")
    
    return {"current_status": state['current_status'], "data": data}

def analysis_node(state):
    data = state['data']
    response = generate_response([
        {"role": "system", "content": ANALYSIS_PROMPT},
        {"role": "user", "content": json.dumps(data)}
    ])
    return {"analysis": json.loads(response)}

def prediction_node(state):
    response = generate_response([
        {"role": "system", "content": PREDICTION_PROMPT},
        {"role": "user", "content": f"Current Status: {state['current_status']}"}
    ])
    return {"prediction": response}

def maintenance_plan_node(state):
    response = generate_response([
        {"role": "system", "content": MAINTENANCE_PLAN_PROMPT},
        {"role": "user", "content": f"Prediction: {state['prediction']}"}
    ])
    return {"maintenance_plan": response}

def priority_assessment_node(state):
    response = generate_response([
        {"role": "system", "content": PRIORITY_ASSESSMENT_PROMPT},
        {"role": "user", "content": f"Prediction: {state['prediction']}, Current Status: {state['current_status']}"}
    ])
    return {"priority": response}

def create_ticket_node(state):
    response = generate_response([
        {"role": "system", "content": CREATE_TICKET_PROMPT},
        {"role": "user", "content": f"Priority: {state['priority']}, Current Status: {state['current_status']}, Prediction: {state['prediction']}, Maintenance Plan: {state['maintenance_plan']}"}
    ])
    return {"ticket": response}

def email_notification_node(state):
    response = generate_response([
        {"role": "system", "content": EMAIL_NOTIFICATION_PROMPT},
        {"role": "user", "content": f"Priority: {state['priority']}, Current Status: {state['current_status']}, Prediction: {state['prediction']}, Maintenance Plan: {state['maintenance_plan']}"}
    ])
    return {"email": response}

def teams_notification_node(state):
    response = generate_response([
        {"role": "system", "content": TEAMS_NOTIFICATION_PROMPT},
        {"role": "user", "content": f"Priority: {state['priority']}, Current Status: {state['current_status']}, Prediction: {state['prediction']}, Maintenance Plan: {state['maintenance_plan']}"}
    ])
    return {"teams": response}

def self_reflection_node(state):
    response = generate_response([
        {"role": "system", "content": SELF_REFLECTION_PROMPT},
        {"role": "user", "content": f"Plan: {state['plan']}, Current Status: {state['current_status']}, Prediction: {state['prediction']}, Maintenance Plan: {state['maintenance_plan']}, Priority: {state['priority']}, Ticket: {state['ticket']}, Email: {state['email']}, Teams: {state['teams']}"}
    ])
    return {"reflection": response}
