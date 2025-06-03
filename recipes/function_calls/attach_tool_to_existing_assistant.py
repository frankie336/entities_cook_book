#! recipes/function_calls/attach_tool_to_existing_assistant.py
"""
Register a “get_flight_times” function‑tool
and attach it to an **existing** assistant with ID "default".
"""

import os
from dotenv import load_dotenv
from projectdavid import Entity

from projectdavid_common.validation import ToolFunction

# --- SDK init ----------------------------------------------------
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ADMIN_API_KEY")
)

# --- Define function schema --------------------------------------
flight_schema = {
    "name": "get_flight_times",
    "description": "Return flight times between two airport codes.",
    "parameters": {
        "type": "object",
        "properties": {
            "departure": {"type": "string", "description": "Departure IATA code"},
            "arrival":   {"type": "string", "description": "Arrival IATA code"}
        },
        "required": ["departure", "arrival"]
    }
}

# --- Create & register tool --------------------------------------
tool = client.tools.create_tool(
    name=flight_schema["name"],
    type="function",
    function=ToolFunction(function=flight_schema)
)
print(f"[✓] Tool created → {tool.id}")


# --- Attach to existing assistant (ID = 'default') ---------------
client.tools.associate_tool_with_assistant(
    tool_id=tool.id,
    assistant_id="plt_ast_9fnJT01VGrK4a9fcNr8z2O"
)
print(f"[✓] Attached tool {tool.id} to assistant 'default'")
