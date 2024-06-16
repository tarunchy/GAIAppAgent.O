
from flask import Flask, Response, request, jsonify
from trt_llama_api import TrtLlmAPI
from utils import messages_to_prompt, completion_to_prompt, ChatMessage, MessageRole, DEFAULT_SYSTEM_PROMPT
import os
import time
import json
import logging
import gc
import torch
from pathlib import Path
from gpustat import GPUStatCollection

# Initialize Flask app
app = Flask(__name__)

gpu_temperature = 0

def check_gpu_temperature():
    try:
        gpu_temperature = max(gpu.temperature for gpu in GPUStatCollection.new_query().gpus)
        if gpu_temperature > 90:
            print("GPU temperature above 90C, shutting down.")
            exit(1)
        return gpu_temperature
    except Exception as e:
        print(f"Error retrieving GPU temperature: {e}")
        return "TError"

def is_present(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False
    if json[key] == None:
        return False
    return True

def read_config(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"The file {file_name} was not found.")
    except json.JSONDecodeError:
        print(f"There was an error decoding the JSON from the file {file_name}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

def get_model_config(config, model_name=None):
    models = config["models"]["supported"]
    selected_model = next((model for model in models if model["name"] == model_name), models[0])
    return {
        "model_path": os.path.join(os.getcwd(), selected_model["metadata"]["model_path"]),
        "engine": selected_model["metadata"]["engine"],
        "tokenizer_path": os.path.join(os.getcwd(), selected_model["metadata"]["tokenizer_path"]),
        "max_new_tokens": selected_model["metadata"]["max_new_tokens"],
        "max_input_token": selected_model["metadata"]["max_input_token"],
        "temperature": selected_model["metadata"]["temperature"]
    }


model_config_file = 'config\\config.json'
config = read_config(model_config_file)
selected_model_name = None

if selected_model_name == None:
    selected_model_name = config["models"].get("selected")

model_config = get_model_config(config, selected_model_name)
trt_engine_path = model_config["model_path"]
trt_engine_name = model_config["engine"]
tokenizer_dir_path = model_config["tokenizer_path"]

# Use the provided arguments
#trt_engine_path = args.trt_engine_path
#trt_engine_name = args.trt_engine_name
#tokenizer_dir_path = args.tokenizer_dir_path
verbose = False
host = "0.0.0.0"
port = "8081"
no_system_prompt = False

# create trt_llm engine object
llm = TrtLlmAPI(
    model_path=trt_engine_path,
    engine_name=trt_engine_name,
    tokenizer_dir=tokenizer_dir_path,
    temperature=0.1,
    max_new_tokens=4096,
    context_window=4096,
    messages_to_prompt=messages_to_prompt,
    completion_to_prompt=completion_to_prompt,
    verbose=False
)


@app.route('/models/Llama2', methods=['POST', 'GET'])
@app.route('/v1/models/Llama2', methods=['POST', 'GET'])
def models():
    resData = {
        "id": "Llama2",
        "object": "model",
        "created": 1675232119,
        "owned_by": "Meta"
    }
    return jsonify(resData)


@app.route('/models', methods=['POST', 'GET'])
@app.route('/v1/models', methods=['POST', 'GET'])
def modelsLlaMA():
    resData = {
        "object": "list",
        "data": [
            {
                "id": "Llama2",
                "object": "model",
                "created": 1675232119,
                "owned_by": "Meta"
            },
        ],
    }
    return jsonify(resData)


@app.route('/chat/completions', methods=['POST'])
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    assert request.headers.get('Content-Type') == 'application/json'
    body = request.get_json()
    stream = False
    temperature = 1.0
    if (is_present(body, "stream")):
        stream = body["stream"]
    if (is_present(body, "temperature")):
        temperature = body["temperature"]
    formatted = False
    if verbose:
        print("/chat/completions called with stream=" + str(stream))

    prompt = ""
    if "messages" in body:
        messages = []
        for item in body["messages"]:
            chat = ChatMessage()
            if "role" in item:
                if item["role"] == 'system':
                    chat.role = MessageRole.SYSTEM
                elif item["role"] == 'user':
                    chat.role = MessageRole.USER
                elif item["role"] == 'assistant':
                    chat.role = MessageRole.ASSISTANT
                elif item["role"] == 'function':
                    chat.role = MessageRole.FUNCTION
                else:
                    print("Missing handling role in message:" + item["role"])
            else:
                print("Missing role in message")

            chat.content = item["content"]
            messages.append(chat)

        system_prompt = ""
        if not no_system_prompt:
            system_prompt = DEFAULT_SYSTEM_PROMPT

        prompt = messages_to_prompt(messages, system_prompt)

        formatted = True
    elif "prompt" in body:
        prompt = body["prompt"]

    if verbose:
        print("INPUT SIZE: " + str(len(prompt)))
        print("INPUT: " + prompt)

    if not stream:
        return llm.complete_common(prompt, True, temperature=temperature, formatted=formatted)
    else:
        return llm.stream_complete_common(prompt, True, temperature=temperature, formatted=formatted)


def process_completions_data(body):
    
    stream = False
    temperature = 1.0
    if (is_present(body, "stream")):
        stream = body["stream"]
    if (is_present(body, "temperature")):
        temperature = body["temperature"]
    formatted = False
    if verbose:
        print("/chat/completions called with stream=" + str(stream))

    prompt = ""
    if "messages" in body:
        messages = []
        for item in body["messages"]:
            chat = ChatMessage()
            if "role" in item:
                if item["role"] == 'system':
                    chat.role = MessageRole.SYSTEM
                elif item["role"] == 'user':
                    chat.role = MessageRole.USER
                elif item["role"] == 'assistant':
                    chat.role = MessageRole.ASSISTANT
                elif item["role"] == 'function':
                    chat.role = MessageRole.FUNCTION
                else:
                    print("Missing handling role in message:" + item["role"])
            else:
                print("Missing role in message")

            chat.content = item["content"]
            messages.append(chat)

        system_prompt = ""
        if not no_system_prompt:
            system_prompt = DEFAULT_SYSTEM_PROMPT

        prompt = messages_to_prompt(messages, system_prompt)

        formatted = True
    elif "prompt" in body:
        prompt = body["prompt"]

    if verbose:
        print("INPUT SIZE: " + str(len(prompt)))
        print("INPUT: " + prompt)

    if not stream:
        return llm.complete_common(prompt, True, temperature=temperature, formatted=formatted)
    else:
        return llm.stream_complete_common(prompt, True, temperature=temperature, formatted=formatted)

@app.route('/llama2', methods=['POST'])
def wrapper_chat_completions():

    global gpu_temperature  # Add this line

    ## Check GPU Temperature
    gpu_stats = GPUStatCollection.new_query()
    try:
        ## Check GPU Temperature
        gpu_stats = GPUStatCollection.new_query()
        for gpu in gpu_stats.gpus:
            gpu_temperature = gpu.temperature
        # Check if temperature is above 90
        if gpu_temperature > 90:
            print("GPU temperature above 90C, shutting down.")
            #subprocess.call(["shutdown", "-h", "now"])
            exit(1)
    except Exception as e:
        print(f"Error retrieving GPU temperature: {e}")
        gpu_temperature = "TError"

    body = request.get_json()
    original_response = process_completions_data(body)
    # Parse the JSON response from the original function
    response_data = original_response.get_json()

    # Extract the message content from the response
    try:
        # Accessing the 'content' field in the response
        message_content = response_data['choices'][0]['message']['content']
        clean_content = message_content.replace('</s>', '').replace('<s>', '')
    except (IndexError, KeyError) as e:
        print(f"Error extracting message content: {e}")
        clean_content = "Error in processing response."

    # Format the response according to the new requirements
    new_response = {
        "gpu_temperature": gpu_temperature,
        "response": clean_content
    }

    # Return the new JSON response
    return jsonify(new_response)

@app.route('/completions', methods=['POST'])
@app.route('/v1/completions', methods=['POST'])
def completion():
    assert request.headers.get('Content-Type') == 'application/json'
    stream = False
    temperature = 1.0
    body = request.get_json()
    if (is_present(body, "stream")):
        stream = body["stream"]
    if (is_present(body, "temperature")):
        temperature = body["temperature"]

    stop_strings = []
    if is_present(body, "stop"):
        stop_strings = body["stop"]

    if verbose:
        print("/completions called with stream=" + str(stream))

    prompt = ""
    if "prompt" in body:
        prompt = body["prompt"]
    

    f = open("prompts.txt", "a")
    f.write("\n---------\n")
    if stream:
        f.write("Completion Input stream:" + prompt)
    else:
        f.write("Completion Input:" + prompt)
    f.close()

    if not no_system_prompt:
        prompt = completion_to_prompt(prompt)

    formatted = True

    if not stream:
        return llm.complete_common(prompt, False, temperature=temperature, formatted=formatted, stop_strings=stop_strings)
    else:
        return llm.stream_complete_common(prompt, False, temperature=temperature, formatted=formatted, stop_strings=stop_strings)


if __name__ == '__main__':
    app.run(host, port=port, debug=True, use_reloader=False, threaded=False)
