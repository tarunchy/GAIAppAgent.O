
# GAIAppAgent.O

## Introduction
GAIAppAgent.O is a comprehensive solution for monitoring applications within an enterprise. The agent periodically checks the health of registered applications, analyzes logs for potential issues, and takes automated actions such as creating ServiceNow tickets, sending notifications, and attempting to restart applications.

## Features
- **Health Check Monitoring**: Periodically polls health check URLs of registered applications.
- **Log Analysis**: Analyzes the last 100 lines of log files for potential issues using OpenAI.
- **Incident Management**: Creates ServiceNow tickets for detected issues or application downtime.
- **Notifications**: Sends notifications via email and Microsoft Teams.
- **Autonomous Actions**: Attempts to restart applications if they are down using Ansible.

## Health Check URL Format
The health check URL should return a JSON response with the following attributes:
- `messages`: Contains the last 100 lines of the log file.
- `support_dl`: Email address of the support distribution list.
- `app_id`: Unique identifier for the application.
- `timestamp`: Timestamp when the health check was generated.

Example:
```json
{
  "messages": "log content here...",
  "support_dl": "support@example.com",
  "app_id": "app123",
  "timestamp": "2024-06-01T12:00:00Z"
}
```

## Setup and Installation
### Prerequisites
- Python 3.8+
- Ansible
- ServiceNow API credentials
- SMTP server for sending emails
- Microsoft Teams Webhook URL
- LLAMA2 13B NVIDIA TRT Engine Accelerated API Endpoint Compliant with OpenAI Chat Completion API interface

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/GAIAppAgent.O.git
    cd GAIAppAgent.O
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure the agent:
    - Update `config.py` with necessary details such as ServiceNow API credentials, SMTP server details, Microsoft Teams webhook URL, and OpenAI API key.

4. Start the agent:
    ```bash
    ./start.sh
    ```

## Configuration
- **Health Check URL**: The health check URL should return a JSON response with the required attributes.
- **Log Analysis**: The agent sends the last 100 lines of logs to OpenAI API to detect issues.
- **ServiceNow**: Configure ServiceNow API credentials in `config.py`.
- **Notifications**: Configure email and Microsoft Teams notification details in `config.py`.

## Directory Structure
```
GAIAppAgent.O
├── Agent
│   ├── app.py
│   ├── config.ini
│   ├── requirements.txt
│   ├── start.sh
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   ├── fhir_kg.png
│   │   ├── images
│   │   │   ├── agent.png
│   │   │   ├── agent1.png
│   │   │   └── agent_flow.png
│   │   └── js
│   │       └── scripts.js
│   ├── templates
│   │   ├── active_apps.html
│   │   ├── edit.html
│   │   ├── index.html
│   │   └── websocket_ui.html
│   ├── utils
│   │   ├── agent_functions.py
│   │   ├── config.ini
│   │   ├── config_loader.py
│   │   ├── notifier.py
│   │   └── state_graph.py
│   └── ws
│       ├── state_graph_ws.py
│       └── websocket_handler.py
├── README.md
├── SmartGridMockApp
│   ├── app.py
│   ├── data.json
│   ├── start.sh
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   └── js
│   │       └── scripts.js
│   ├── stop.sh
│   └── templates
│       └── dashboard.html
├── ansible
│   ├── manage_smart_grid_app.yml
│   └── test_host.yml
├── api_app
│   ├── README.md
│   ├── app.py
│   ├── config
│   │   ├── app_config.json
│   │   ├── config.json
│   │   └── preferences.json
│   ├── prompts.txt
│   ├── requirements.txt
│   ├── start.bat
│   ├── trt_llama_api.py
│   ├── utils.py
│   └── verify_install.py
├── requirements.txt
├── setup_project.sh
└── start.sh
```
17 directories, 45 files

## Technology Flow
- **Browser**: User interacts with the application through a browser.
- **Apache Web Server**: Handles incoming requests and forwards them to the Flask Python App.
- **Flask Python App Agent**: Manages health checks, log analysis, and incident management.
- **API Layer**: Utilizes Meta's 13B Model exposed as REST API for advanced processing.
- **NVIDIA GPU**: Accelerates AI operations using the RTX 3090 Ti.

## Detailed Design and Workflow
### Health Check Monitoring
1. The agent periodically (every hour) sends a GET request to the health check URL of each registered application.
2. The health check URL returns a JSON response containing the log messages, support DL, app ID, and timestamp.

### Log Analysis
1. The agent sends the log messages to OpenAI API.
2. The OpenAI API analyzes the logs and detects potential issues.
3. If an issue is detected, the agent creates a ServiceNow ticket and sends notifications to the support DL and Microsoft Teams.

### Incident Management
1. If the health check URL returns a non-200 response, the agent creates a ServiceNow ticket and sends notifications.
2. The agent uses Ansible to SSH or WinRM into the VM and attempts to restart the application.

### Notifications
1. The agent sends notifications via email and Microsoft Teams based on the analysis and incident management results.
2. The email content and Microsoft Teams messages are generated using OpenAI API to ensure clarity and detailed steps for the support team.

### Autonomous Actions
1. The agent attempts to restart applications if they are down using predefined Ansible playbooks.
2. The Ansible playbooks are configured to handle both Linux and Windows environments.

## Example Workflow
1. **Application Registration**: Admin registers an application with its health check URL, support DL, and other details.
2. **Periodic Health Check**: The agent polls the health check URL every hour.
3. **Log Analysis**: The agent analyzes the logs using OpenAI API.
4. **Issue Detection**: If an issue is detected, the agent creates a ServiceNow ticket and sends notifications.
5. **Application Downtime**: If the application is down, the agent attempts to restart it using Ansible and notifies the support team.

## Future Enhancements
- Implement more advanced log analysis using machine learning models.
- Integrate with additional notification systems (e.g., Slack, PagerDuty).
- Enhance self-healing capabilities with more sophisticated Ansible playbooks.

## Advanced Features
### Root Cause Analysis and Reflection
Within our chain graph, we have two critical nodes: the Root Cause Analysis node and the Reflect node. These nodes interact in a loop for three iterations. The Root Cause Analysis node prompts the LLM to identify the issue, and the Reflect node reviews and updates the findings. This back-and-forth ensures a thorough and accurate diagnosis.

These solutions are possible thanks to the excellent framework provided by LANG chain and LANG graph, Meta's LLAMA 13B accelerated model by TRT engine, and, of course, the backbone powered by NVIDIA GPU. Here, we used the RTX 3090 Ti.

Welcome to the future, where you no longer have to wake up in the middle of the night for app support issues. Let AutoHealChain's AI agent do the hard work for you, ensuring your systems are always running smoothly and securely.

## Image of Agent Flow
![Agent Flow](https://github.com/tarunchy/GAIAppAgent.O/tree/main/Agent/static/images/agent_flow.png)

AutoHealChain streamlines incident management, providing fast and efficient self-healing capabilities for app support. Thank you for watching. For further details, design code, and documentation, please refer to our code repository.
