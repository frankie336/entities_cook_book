import os
import json
import time
from projectdavid import Entity
from dotenv import load_dotenv

load_dotenv()

client = Entity(api_key=os.getenv("ENTITIES_API_KEY"))


def get_flight_times(tool_name, arguments):
    if tool_name == "get_flight_times":
        return json.dumps(
            {
                "status": "success",
                "message": f"Flight from {arguments.get('departure')} to {arguments.get('arrival')}: 4h 30m",
                "departure_time": "10:00 AM PST",
                "arrival_time": "06:30 PM EST",
            }
        )
    return json.dumps(
        {"status": "success", "message": f"Executed tool '{tool_name}' successfully."}
    )


user_id = "user_kUKV8octgG2aMc7kxAcD3i"
assistant_id = "default"
thread = client.threads.create_thread(participant_ids=[user_id])

message = client.messages.create_message(
    thread_id=thread.id,
    role="user",
    content="Please fetch me the flight times between LAX and NYC, JFK",
    assistant_id=assistant_id,
)

run = client.runs.create_run(assistant_id=assistant_id, thread_id=thread.id)

sync_stream = client.synchronous_inference_stream
sync_stream.setup(
    user_id=user_id,
    thread_id=thread.id,
    assistant_id=assistant_id,
    message_id=message.id,
    run_id=run.id,
    api_key=os.getenv("HYPERBOLIC_API_KEY"),
)

# --- Stream initial LLM response ---
for chunk in sync_stream.stream_chunks(
    provider="Hyperbolic",
    model="hyperbolic/deepseek-ai/DeepSeek-V3-0324",
    timeout_per_chunk=15.0,
    api_key=os.getenv("HYPERBOLIC_API_KEY"),
):
    content = chunk.get("content", "")
    if content:
        print(content, end="", flush=True)

# --- Function call execution ---
try:
    action_was_handled = client.runs.poll_and_execute_action(
        run_id=run.id,
        thread_id=thread.id,
        assistant_id=assistant_id,
        tool_executor=get_flight_times,
        actions_client=client.actions,
        messages_client=client.messages,
        timeout=45.0,
        interval=1.5,
    )

    if action_was_handled:
        print("\n[Tool executed. Generating final response...]\n")
        sync_stream.setup(
            user_id=user_id,
            thread_id=thread.id,
            assistant_id=assistant_id,
            message_id="regenerated",
            run_id=run.id,
            api_key=os.getenv("HYPERBOLIC_API_KEY"),
        )
        for final_chunk in sync_stream.stream_chunks(
            provider="Hyperbolic",
            model="hyperbolic/deepseek-ai/DeepSeek-V3-0324",
            timeout_per_chunk=15.0,
            api_key=os.getenv("HYPERBOLIC_API_KEY"),
        ):
            content = final_chunk.get("content", "")
            if content:
                print(content, end="", flush=True)
except Exception as e:
    print(f"\n[Error during tool execution or final stream]: {str(e)}")
