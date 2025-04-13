# ---------------------------------
# Install & Import the projectdavid
# SDK.
# ---------------------------------
import os
from dotenv import load_dotenv

from projectdavid import Entity

load_dotenv()
client = Entity(api_key=os.getenv("ENTITIES_API_KEY"))


# -------------------------------------
# Create a user
# -------------------------------------

user = client.users.create_user(name="test_user336")
print(f"Created user {user.id}")

# Created user user_oKwebKcvx95018NPtzTaGB

# -------------------------------------
# Create an assistant
# -------------------------------------

assistant = client.assistants.create_assistant(
    name="test_assistant",
    instructions="You are a helpful assistant" "working at an airport.",
)
print(f"created assistant {assistant.id}")

# created assistant asst_XXPNWcoSEqDOFNuvLLv9vJ

# -------------------------------------
# Define the function structure
# -------------------------------------

function_definition = {
    "function": {
        "name": "get_flight_times",
        "description": "Get the flight times between two cities.",
        "parameters": {
            "type": "object",
            "properties": {
                "departure": {
                    "type": "string",
                    "description": "The departure city (airport code).",
                },
                "arrival": {
                    "type": "string",
                    "description": "The arrival city (airport code).",
                },
            },
            "required": ["departure", "arrival"],
        },
    }
}
# -------------------------------------------------------
#  Import the function call validation object
#  This will ensure that your definitions are correctly
#  formed to @OpenAI structure
# --------------------------------------------------------
from projectdavid_common.schemas.tools import ToolFunction

try:
    print("Creating new tool...")

    # 1. Create the ToolFunction object explicitly
    tool_func_obj = ToolFunction(function=function_definition["function"])

    # 2. Call create_tool, passing the object
    tool = client.tools.create_tool(
        name=function_definition["function"]["name"],
        type="function",
        function=tool_func_obj,
    )
    print(f"Created tool {tool.id}")

    # -------------------------------------
    # Attach the tool to your assistant
    # -------------------------------------

    assistant_id = "assistant asst_XXPNWcoSEqDOFNuvLLv9vJ"

    client.tools.associate_tool_with_assistant(
        tool_id=tool.id, assistant_id=assistant_id
    )

    print(f"attached tool: {tool.id} to assistant: ")

except ValueError as e:
    print(f"ERROR: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# Created tool tool_DFt6Zz6BEX4COKZGz8tTd4
