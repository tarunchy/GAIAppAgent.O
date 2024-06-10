import configparser

def load_config_ini():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

config = load_config_ini()
json_config_path = config['settings']['json_config_path']

def load_apps_config():
    with open(json_config_path, 'r') as f:
        return json.load(f)

def save_apps_config(apps_config):
    with open(json_config_path, 'w') as f:
        json.dump(apps_config, f, indent=4)
