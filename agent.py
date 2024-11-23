import os
import subprocess
import signal
import sys
import logging
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import shlex

def basic_config(): 
    load_dotenv()
    api_key = os.getenv("API_KEY")
    model_name = os.getenv("MODEL_NAME") or "gpt-4o-mini"
    logging.basicConfig(filename="iptables_changes.log", level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    return api_key, model_name

def list_rules(*args) -> str:
    try:
        command = "sudo iptables -L -n -v"
        result = subprocess.run(command.split(), capture_output=True, text=True, check=True)
        logging.info(f"Command: {command} executed.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error listing the rules: {e}"



def is_valid_iptables_command(rule: str) -> bool:
    """
    Validates that the command contains both 'sudo' and 'iptables' and doesn't contain additional commands.
    """
    forbidden_tokens = {'&&', '||', ';', '|', '&', '>', '<', '`', '$'}
    tokens = shlex.split(rule)
    if len(tokens) < 2:
        return False
    if tokens[0] != 'sudo' or tokens[1] != 'iptables':
        return False

    for tok in tokens[2:]:
        if any(char in forbidden_tokens for char in tok):
            return False
    return True


def modify_rule(rule: str) -> str:
    command = f"sudo {rule}"
    if not is_valid_iptables_command(command):
        logging.warning(f"Invalid command format: {command}")
        return "Invalid command format. Rule not added."

    try:
        decision = input("Are you sure you want to run the following command? (y/n)\n" + command + "\n")
        if decision.lower() == "y":
            subprocess.run(command.split(), check=True)
            logging.info(f"Command: {command} executed.")
            return f"Command: {rule} executed."
        else:
            logging.info(f"Command: {command} not executed.")
            return f"Command: {command} not executed."
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command: {command}, Error: {e}")
        return f"Error modifying the rule: {e}"

def agent_setup(api_key, model_name):
    list_rules_tool = Tool(name="list_rules", func=list_rules, description="Lists all the current rules in iptables.")
    modify_rule_tool = Tool(name="modify_rule", func=modify_rule, description="Adds or deletes a rule in iptables.")
    llm = ChatOpenAI(api_key=api_key, model=model_name, temperature=0.0)
    tools = [list_rules_tool, modify_rule_tool]

    prompt_template = """
    You are an expert security system that can interact with iptables to manage firewall rules. 
    The user will provide a description of the task they want to perform, such as 'Allow HTTP traffic' or 'Delete a specific rule', 
    and you need to generate the corresponding iptables rule(s). Also, the user may ask you for security recommendations, 
    and you should provide them with the best practices for iptables.

    The current iptables rules are as follows:
    {current_rules}

    Your task:
    1. Understand the user's request, you will receive the current iptables list of the user.
    2. If the user wants to allow or block traffic, generate the appropriate iptables rule.
    3. It's important that you give the output in the same order as the user says.
    4. Use the provided tools to add or remove rules from iptables, you MUST include the whole command.
    5. Provide feedback to the user about what was done.

    The tools you have access to:
    - list_rules: List all current iptables rules.
    - modify_rule: Modify (add or delete) a rule in iptables.

    {input}

    {agent_scratchpad}
    """
    prompt = PromptTemplate(input_variables=["input", "agent_scratchpad", "current_rules"], template=prompt_template)
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

def signal_handler(sig, frame):
    print('\nGracefully shutdown...\n')
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    api_key, model_name = basic_config()
    agent_executor = agent_setup(api_key, model_name)

    while True:
        user_input = input("Describe the action you want to perform (e.g., 'Allow HTTP traffic', 'Delete rule X'): ")
        current_rules = list_rules()
        context_input = {"input": user_input, "agent_scratchpad": "", "current_rules": current_rules}
        response = agent_executor.invoke(context_input)