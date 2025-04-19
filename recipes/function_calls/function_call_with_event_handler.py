"""
Cookbook Demo: Function‑Call Round‑Trip  (Together AI) – SSE event‑driven edition
-------------------------------------------------------------------------------
• Sends a user message that triggers the function.
• Executes the tool server‑side via SSE watch_run_events.
• Streams the final assistant reply using the “regenerated” message_id.
"""

import json
import os
import threading
from dotenv import load_dotenv
from projectdavid import Entity

# ------------------------------------------------------------------
# 0.  SDK init + env
# ------------------------------------------------------------------
load_dotenv()
BASE_URL          = os.getenv("BASE_URL", "http://localhost:9000")
ENTITIES_KEY      = os.getenv("ENTITIES_API_KEY")
USER_ID           = os.getenv("ENTITIES_USER_ID")
ASSISTANT_ID      = "default"
MODEL_ID          = "hyperbolic/deepseek-ai/DeepSeek-V3-0324"
PROVIDER_KW       = "Hyperbolic"
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")

client = Entity(base_url=BASE_URL, api_key=ENTITIES_KEY)

# ------------------------------------------------------------------
# 1.  Tool executor (must return JSON‑string or str)
# ------------------------------------------------------------------
def get_flight_times(tool_name: str, args: dict) -> str:
    if tool_name == "get_flight_times":
        return json.dumps({
            "status":        "success",
            "departure":     args["departure"],
            "arrival":       args["arrival"],
            "duration":      "4h 30m",
            "departure_time":"10:00 AM PST",
            "arrival_time":  "06:30 PM EST"
        })
    raise ValueError(f"Unknown tool: {tool_name}")

# ------------------------------------------------------------------
# 2.  Thread + user message + run
# ------------------------------------------------------------------
thread = client.threads.create_thread(participant_ids=[USER_ID])
message = client.messages.create_message(
    thread_id=thread.id,
    role="user",
    content="Please fetch me the flight times between LAX and JFK.",
    assistant_id=ASSISTANT_ID
)
run = client.runs.create_run(assistant_id=ASSISTANT_ID, thread_id=thread.id)

# ------------------------------------------------------------------
# 3.  Stream initial LLM response (with the function_call chunk)
# ------------------------------------------------------------------
stream = client.synchronous_inference_stream
stream.setup(
    user_id=USER_ID,
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID,
    message_id=message.id,
    run_id=run.id,
    api_key=HYPERBOLIC_API_KEY
)
print("\n[▶] Initial stream …\n")
for chunk in stream.stream_chunks(provider=PROVIDER_KW, model=MODEL_ID, timeout_per_chunk=30.0):
    if chunk.get("type") == "function_call":
        print(f"\n[function_call] → {chunk['name']}({chunk['arguments']})\n")
    else:
        print(chunk.get("content", ""), end="", flush=True)

# ------------------------------------------------------------------
# 4.  Listen for action_required via SSE, execute & submit tool result
# ------------------------------------------------------------------
print("\n[▶] Waiting for action_required event …")
client.runs.watch_run_events(
    run_id=run.id,
    tool_executor=get_flight_times,
    actions_client=client.actions,
    messages_client=client.messages,
    assistant_id=ASSISTANT_ID,
    thread_id=thread.id,
)
print("[✓] Tool executed, streaming final answer …\n")

# ------------------------------------------------------------------
# 5.  Stream final assistant response with the **same** “regenerated” logic
# ------------------------------------------------------------------
stream.setup(
    user_id=USER_ID,
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID,
    # <-- note this matches exactly your polling example:
    message_id="regenerated",
    run_id=run.id,
    api_key=HYPERBOLIC_API_KEY
)
for chunk in stream.stream_chunks(provider=PROVIDER_KW, model=MODEL_ID, timeout_per_chunk=30.0):
    print(chunk.get("content", ""), end="", flush=True)

print("\n\n--- End of Stream ---")
