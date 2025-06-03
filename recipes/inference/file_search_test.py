"""
Basic Inference Streaming Demo
------------------------------
Demonstrates:
1. Creating an assistant and thread
2. Sending a user message
3. Initiating a run
4. Streaming the assistant response via Hyperbolic provider
"""
import os
import time

from dotenv import load_dotenv
from projectdavid import Entity

from recipes.function_calls.basic_function_call_handling import ASSISTANT_ID

# Load environment variables from .env
load_dotenv()

print(os.getenv("ENTITIES_API_KEY"))



# ── Initialize the SDK client ────────────────────────────────────────────
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY")
)


API_KEY = os.getenv("HYPERBOLIC_API_KEY")
MODEL = "hyperbolic/deepseek-ai/DeepSeek-V3-0324"
PROVIDER = "Hyperbolic"


def main():
    user_id = os.getenv("ENTITIES_USER_ID")

    ASSISTANT_ID = "plt_ast_9fnJT01VGrK4a9fcNr8z2O"

    # ── Thread Creation ──────────────────────────
    # Threads can be reused.
    # ─────────────────────────────────────────────

    print("[+] Creating thread...")
    thread = client.threads.create_thread(participant_ids=[user_id])
    actual_thread_id = thread.id
    print(f"[✓] Thread created: {actual_thread_id}")

    # ── Message Creation ──────────────────────────
    print("[+] Creating user message...")
    message = client.messages.create_message(
        thread_id=actual_thread_id,
        role="user",

        # content="Explain a black hole to me in pure mathematical terms",

        content="Use file search to response to the following: Who is the most insidious  type of gym person, and why?",

        assistant_id=ASSISTANT_ID,
    )
    print(f"[✓] Message created: {message.id}")


    # ── Run Creation ──────────────────────────

    print("[+] Creating run...")
    run = client.runs.create_run(
        assistant_id=ASSISTANT_ID,
        thread_id=actual_thread_id
    )
    print(f"[✓] Run created: {run.id}")

    # --- Set Up Streaming ---
    print("[*] Setting up synchronous stream...")
    sync_stream = client.synchronous_inference_stream
    sync_stream.setup(
        user_id=user_id,
        thread_id=actual_thread_id,
        assistant_id=ASSISTANT_ID,
        message_id=message.id,
        run_id=run.id,
        api_key=API_KEY,
    )
    print("[✓] Stream setup complete.")

    # --- Start Streaming ---
    print("[▶] Streaming response:\n")
    try:
        for chunk in sync_stream.stream_chunks(
            provider=PROVIDER,
            model=MODEL,
            timeout_per_chunk=60.0,
        ):
            content = chunk.get("content", "")
            if content:
                print(content, end="", flush=True)
        print("\n--- End of Stream ---")
    except Exception as e:
        print(f"\n[!] Stream Error: {e}")

    print("[✓] Script finished.")

if __name__ == "__main__":
    main()
