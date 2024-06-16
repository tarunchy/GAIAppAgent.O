import json
import os

# Define the file path to the configuration file.
config_file_path = 'config/config.json'

# Function to read the configuration file.
def read_config(file_path):
    try:
        # Open and read the file.
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Return None if the file is not found.
        return None

# Function to check if the engine file exists.
def check_engine_exists(model_path, engine):
    # Construct the full path to the engine file.
    engine_path = os.path.join(os.getcwd(), model_path, engine)
    # Check if the file exists at the path.
    return os.path.exists(engine_path)

# Function to save the configuration file.
def save_config(file_path, data):
    try:
        # Open and write the updated data to the file.
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        return True
    except Exception as e:
        # Print an error message if saving fails.
        print(f"Error saving the file: {e}")
        return False

# Read the configuration file.
config = read_config(config_file_path)
installed_model_found = False
if config:
    # Iterate through each model in the configuration.
    for model in config['models']['supported']:
        # Retrieve model path and engine file name.
        model_path = model['metadata']['model_path']
        engine = model['metadata']['engine']
        # Update the 'installed' flag based on engine file existence.
        model['installed'] = check_engine_exists(model_path, engine)
        
        if model['installed'] and not installed_model_found:
            config['models']['selected'] = model['name']
            installed_model_found = True

    # Save the updated configuration back to the file.
    if save_config(config_file_path, config):
        # Print confirmation and the updated configuration.
        print("App running with config\n", json.dumps(config, indent=4))
    else:
        # Print an error message if saving fails.
        print("Failed to save the updated configuration.")
