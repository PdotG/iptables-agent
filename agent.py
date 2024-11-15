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

# Load the OpenAI API key from the .env file
load_dotenv()
OPEN_API_KEY = os.getenv("OPEN_API_KEY")

# Logging configuration
logging.basicConfig(filename="iptables_changes.log", level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def list_rules(*args) -> str:
    """
    Lists all the current rules in iptables.
    """
    try:
        command = "sudo iptables -L -n -v"
        result = subprocess.run(command.split(), capture_output=True, text=True, check=True)
        logging.info(f"Command: {command} executed.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error listing the rules: {e}"

def modify_rule(rule: str) -> str:
    """
    Adds or deletes a rule based on the action parameter ('add' or 'delete').
    """
    
    try:
        command = f"sudo {rule}"  # Use 'A' for add, 'D' for delete
        decision = input("Are you sure you want to run the following command? (y/n)\n" + command + "\n");
        if decision == "y":
           subprocess.run(command.split(), check=True)
           # Log the change in a log file
           logging.info(f"Command: sudo {rule} added.")
           return f"Command: sudo {rule} added."
        
        return f"Command: sudo {rule} not added."
    except subprocess.CalledProcessError as e:
        return f"Error modifying the rule: {e}"

# Tools
list_rules_tool = Tool(name="list_rules", func=list_rules, description="Lists all the current rules in iptables.")
modify_rule_tool = Tool(name="modify_rule", func=modify_rule, description="Adds or deletes a rule in iptables.")

# Set up OpenAI API model
llm = ChatOpenAI(api_key=str(OPEN_API_KEY), model="gpt-4o-mini", temperature=0.0)

tools = [list_rules_tool, modify_rule_tool]

# Prompt to include user's rules and give instructions to the agent
prompt_template = """
You are an expert security system that can interact with iptables to manage firewall rules. The user will provide a description of the task they want to perform, such as 'Allow HTTP traffic' or 'Delete a specific rule', and you need to generate the corresponding iptables rule(s).
Also, the user may ask you for security recommendations, and you should provide them with the best practices for iptables.

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

def signal_handler(sig, frame):
    print('\nGracefully shutdown...\n')
    sys.exit(0)

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)
    while True:
        user_input = input("Describe the action you want to perform (e.g., 'Allow HTTP traffic', 'Delete rule X'): ")

        current_rules = list_rules()

        context_input = {"input": user_input, "agent_scratchpad": "", "current_rules": current_rules}

        response = agent_executor.invoke(context_input)
