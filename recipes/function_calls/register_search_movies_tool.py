#! recipes/function_calls/register_search_movies_tool.py
"""
Register the `search_movies` function tool and attach it to the default assistant.
This enables function calling for MovieLens-style semantic vector queries.
"""

import os
from dotenv import load_dotenv
from projectdavid import Entity
from projectdavid_common.schemas.tools import ToolFunction

# ─── 0. Load environment and init SDK ────────────────────────────────────────
load_dotenv()

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY")
)

# ─── 1. Define tool schema for movie vector search ───────────────────────────
search_schema = {
    "name": "search_movies",
    "description": "Semantic search in the MovieLens vector store",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Freeform user query to search for a movie"
            },
            "top_k": {
                "type": "integer",
                "description": "How many similar results to return",
                "default": 5
            },
            "store_id": {
                "type": "string",
                "description": "The vector store to search in"
            }
        },
        "required": ["query"]
    }
}

# ─── 2. Register tool (if not already registered) ────────────────────────────
tool = client.tools.create_tool(
    name=search_schema["name"],
    type="function",
    function=ToolFunction(function=search_schema)
)
print(f"[✓] Tool registered → {tool.id} ({tool.name})")

# ─── 3. Attach to default assistant ──────────────────────────────────────────
assistant_id = "default"

client.tools.associate_tool_with_assistant(
    tool_id=tool.id,
    assistant_id=assistant_id
)

print(f"[✓] Attached tool '{tool.name}' to assistant '{assistant_id}'")
