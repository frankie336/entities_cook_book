"""
Cookbook Snippet: Registering a Function‑Tool
--------------------------------------------
• Create a demo user
• Spin up an assistant
• Define a JSON‑schema function
• Register the function as a tool
• Attach the tool to the assistant
"""

import os
from dotenv import load_dotenv
from projectdavid import Entity
from projectdavid_common.schemas.tools import ToolFunction

# ------------------------------------------------------------------
# 0. Environment + SDK init
# ------------------------------------------------------------------
load_dotenv()

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY")
)

# ------------------------------------------------------------------
# 1. Create a throw‑away user (or look yours up)
# ------------------------------------------------------------------
user = client.users.create_user(name="tool_demo_user")
print(f"[✓] user ➜ {user.id}")

# ------------------------------------------------------------------
# 2. Create an assistant
# ------------------------------------------------------------------
assistant = client.assistants.create_assistant(
    name="airport_assistant",
    instructions="You are a helpful assistant working at an airport."
)
print(f"[✓] assistant ➜ {assistant.id}")

# ------------------------------------------------------------------
# 3. Define the function schema
# ------------------------------------------------------------------
flight_func_schema = {
    "name": "get_flight_times",
    "description": "Return flight times between two airport codes.",
    "parameters": {
        "type": "object",
        "properties": {
            "departure": {
                "type": "string",
                "description": "IATA code for the departure airport."
            },
            "arrival": {
                "type": "string",
                "description": "IATA code for the arrival airport."
            }
        },
        "required": ["departure", "arrival"]
    }
}

# Validate & wrap the schema
tool_func = ToolFunction(function=flight_func_schema)

# ------------------------------------------------------------------
# 4. Register the tool
# ------------------------------------------------------------------
tool = client.tools.create_tool(
    name=flight_func_schema["name"],
    type="function",
    function=tool_func
)
print(f"[✓] tool ➜ {tool.id}")

# ------------------------------------------------------------------
# 5. Attach tool to the assistant
# ------------------------------------------------------------------
client.tools.associate_tool_with_assistant(
    tool_id=tool.id,
    assistant_id=assistant.id
)
print(f"[✓] attached {tool.id} → {assistant.id}")
