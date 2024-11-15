# iptables Management Agent

This project provides an interactive agent to manage `iptables` firewall rules. It utilizes OpenAI's GPT-4-based LLM for intelligent rule generation and modification, integrating tools for listing and modifying `iptables` configurations. The agent also provides security recommendations based on user input.

## Features

- **List Current Rules**: View all existing `iptables` rules.
- **Modify Rules**: Add or remove `iptables` rules interactively.
- **Smart Suggestions**: Generate appropriate rules based on user requests like "Allow HTTP traffic."
- **Logging**: Maintains a log of all changes made to the firewall.

## Requirements

- Python 3.8+
- `iptables` installed and accessible with `sudo`.
- OpenAI API key.
- `langchain` library and related dependencies.

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/PdotG/iptables-agent.git
cd iptables-agent
```

### 2. Install Dependencies

Install required Python libraries:

```bash
pip -r requierements.txt
```

### 3. Set Up Environment Variables

Create a .env file in the project root directory and add your OpenAI API key:

```bash
OPEN_API_KEY=your_openai_api_key
```

### 4. Grant Required Permissions

The agent requires sudo privileges to modify iptables. Ensure your user has the appropriate permissions.
## Usage
Run the Agent

Execute the script:

python agent.py

Interact with the Agent

    Provide input such as:
        Allow HTTP traffic
        Block incoming traffic on port 22
    The agent will:
        List the current rules.
        Generate a rule based on your request.
        Ask for confirmation before applying changes.
        Log all changes in iptables_changes.log.

Example Workflow

    User Input: Allow HTTP traffic
    Agent Response:
        Lists current rules.
        Proposes the iptables command for allowing HTTP traffic.
        Requests confirmation before executing the command.
        Logs the change.

Prompt Details

The agent follows a structured prompt to:

    Understand user requests.
    Use tools for listing or modifying rules.
    Provide feedback on actions taken.

Tools Available

    list_rules: Lists all current rules in iptables.
    modify_rule: Adds or deletes a rule.

## Logging

All changes to iptables are logged in iptables_changes.log with timestamps for auditing.
## Graceful Shutdown

Use Ctrl+C to terminate the program safely. A signal handler ensures clean shutdown.
Security Notes

    Ensure the system running the agent is secure and has minimal exposure to unauthorized users.
    Audit iptables_changes.log regularly to monitor changes.

