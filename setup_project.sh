#!/bin/bash

# Create directory structure
mkdir -p agent ansible scripts

# Create README.md
cat <<EOL > README.md
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
- \`messages\`: Contains the last 100 lines of the log file.
- \`support_dl\`: Email address of the support distribution list.
- \`app_id\`: Unique identifier for the application.
- \`timestamp\`: Timestamp when the health check was generated.

Example:
\`\`\`json
{
  "messages": "log content here...",
  "support_dl": "support@example.com",
  "app_id": "app123",
  "timestamp": "2024-06-01T12:00:00Z"
}
\`\`\`

## Setup and Installation
### Prerequisites
- Python 3.8+
- Ansible
- ServiceNow API credentials
- SMTP server for sending emails
- Microsoft Teams Webhook URL
- OpenAI API key

### Installation
1. Clone the repository:
    \`\`\`bash
    git clone https://github.com/yourusername/GAIAppAgent.O.git
    cd GAIAppAgent.O
    \`\`\`

2. Install dependencies:
    \`\`\`bash
    pip install -r requirements.txt
    \`\`\`

3. Configure the agent:
    - Update \`config.py\` with necessary details such as ServiceNow API credentials, SMTP server details, Microsoft Teams webhook URL, and OpenAI API key.

4. Start the agent:
    \`\`\`bash
    python agent/main.py
    \`\`\`

## Configuration
- **Health Check URL**: The health check URL should return a JSON response with the required attributes.
- **Log Analysis**: The agent sends the last 100 lines of logs to OpenAI API to detect issues.
- **ServiceNow**: Configure ServiceNow API credentials in \`config.py\`.
- **Notifications**: Configure email and Microsoft Teams notification details in \`config.py\`.

## Directory Structure
- **agent/**: Contains the main logic for the agent, including health checks, log analysis, ServiceNow integration, notifications, and Ansible playbook execution.
- **ansible/**: Contains Ansible playbooks for restarting applications on Linux and Windows.
- **scripts/**: Contains setup and installation scripts.
- **requirements.txt**: Lists the Python dependencies required for the project.

## Contributing
We welcome contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

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
EOL

# Create agent files
touch agent/{main.py,config.py,health_check.py,log_analyzer.py,service_now.py,notifications.py,ansible_playbook.py}

# Create ansible files
touch ansible/{restart_linux_app.yml,restart_windows_app.yml}

# Create requirements.txt
cat <<EOL > requirements.txt
Flask
Flask-SQLAlchemy
Flask-Mail
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
requests
EOL

# Create script files
touch scripts/{setup_agent.sh,install_dependencies.sh}

# Make scripts executable
chmod +x scripts/{setup_agent.sh,install_dependencies.sh}

echo "Project structure created successfully."
