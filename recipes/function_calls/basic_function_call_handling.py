"""
Cookbook Demo: Function‑Call Round‑Trip  (Together AI)
-----------------------------------------------------
• Uses an existing assistant  (ID = "default") that already has the
  `get_flight_times` function‑tool attached.
• Sends a user message that should trigger the function.
• Executes the tool server‑side and streams the final assistant reply.
"""

import json
import os
from dotenv import load_dotenv
from projectdavid import Entity

# ------------------------------------------------------------------
# 0.  SDK init + env
# ------------------------------------------------------------------
load_dotenv()

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY")
)

USER_ID      = os.getenv("ENTITIES_USER_ID")          # e.g. user_xxx…
ASSISTANT_ID = "default"                              # existing assistant
MODEL_ID     = "hyperbolic/deepseek-ai/DeepSeek-V3-0324"
PROVIDER_KW  = "TogetherAI"                           # router reads model path anyway
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")          # provider key

# ------------------------------------------------------------------
# 1.  Tool executor  (runs locally for this demo)
# ------------------------------------------------------------------
def get_flight_times(tool_name: str, arguments: dict) -> str:
    """Fake flight‑time lookup."""
    if tool_name == "get_flight_times":
        return json.dumps({
            "status": "success",
            "departure": arguments.get("departure"),
            "arrival":   arguments.get("arrival"),
            "duration":  "4h 30m",
            "departure_time": "10:00 AM PST",
            "arrival_time":   "06:30 PM EST"
        })
    return json.dumps({"status": "error", "message": f"unknown tool '{tool_name}'"})

# ------------------------------------------------------------------
# 2.  Thread + message + run
# ------------------------------------------------------------------
thread   = client.threads.create_thread(participant_ids=[USER_ID])
message  = client.messages.create_message(
    thread_id=thread.id,
    role="user",
    content="Please fetch me the flight times between LAX and JFK.",
    assistant_id=ASSISTANT_ID
)
run = client.runs.create_run(assistant_id=ASSISTANT_ID, thread_id=thread.id)

# ------------------------------------------------------------------
# 3.  Stream initial LLM response (should contain the function call)
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
for chunk in stream.stream_chunks(
        provider=PROVIDER_KW,
        model=MODEL_ID,
        timeout_per_chunk=30.0):
    if chunk.get("type") == "function_call":
        print(f"\n[function_call] → {chunk['name']}({chunk['arguments']})\n")
    else:
        print(chunk.get("content", ""), end="", flush=True)

# ------------------------------------------------------------------
# 4.  Poll run → execute tool → send tool result
# ------------------------------------------------------------------
handled = client.runs.poll_and_execute_action(
    run_id=run.id,
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID,
    tool_executor=get_flight_times,
    actions_client=client.actions,
    messages_client=client.messages,
    timeout=5.0,
    interval=0.1
)

# ------------------------------------------------------------------
# 5.  Stream final assistant response
# ------------------------------------------------------------------
if handled:
    print("\n\n[✓] Tool executed, streaming final answer …\n")

    stream.setup(
        user_id=USER_ID,
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        message_id="regenerated",
        run_id=run.id,
        api_key=HYPERBOLIC_API_KEY
    )

    for chunk in stream.stream_chunks(
            provider=PROVIDER_KW,
            model=MODEL_ID,
            timeout_per_chunk=30.0):
        print(chunk.get("content", ""), end="", flush=True)

    print("\n\n--- End of Stream ---")
else:
    print("\n[!] No function call detected or execution failed.")
