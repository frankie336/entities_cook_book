"""
Cookbook Demo: Function-Call Round-Trip  (Together AI)
-----------------------------------------------------
• Uses an existing assistant (ID = "default") that already has the
  `get_flight_times` function-tool attached.
• Sends a user message that should trigger the function.
• Executes the tool server-side and streams the final assistant reply,
  hiding any <fc> … </fc> payload from the console.
"""
import json
import os
import re
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

USER_ID            = os.getenv("ENTITIES_USER_ID")
ASSISTANT_ID       = "plt_ast_9fnJT01VGrK4a9fcNr8z2O"
MODEL_ID           = "hyperbolic/meta-llama/Meta-Llama-3-70B-Instruct"
PROVIDER_KW        = "Hyperbolic"
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")

# ------------------------------------------------------------------
#  Function-call suppressor (regex-based)
# ------------------------------------------------------------------
class FunctionCallSuppressor:
    OPEN_RE  = re.compile(r"<\s*fc\s*>",  re.IGNORECASE)
    CLOSE_RE = re.compile(r"</\s*fc\s*>", re.IGNORECASE)

    def __init__(self):
        self.in_fc = False
        self.buf   = ""

    def filter_chunk(self, chunk: str) -> str:
        self.buf += chunk
        out = ""

        while self.buf:
            if not self.in_fc:
                m = self.OPEN_RE.search(self.buf)
                if not m:
                    out += self.buf
                    self.buf = ""
                    break

                out += self.buf[:m.start()]
                print("[SUPPRESSOR] <fc> detected")
                self.buf = self.buf[m.end():]
                self.in_fc = True
            else:
                m = self.CLOSE_RE.search(self.buf)
                if not m:
                    break  # wait for more tokens
                print("[SUPPRESSOR] </fc> detected — block suppressed")
                self.buf = self.buf[m.end():]
                self.in_fc = False

        return out

# ------------------------------------------------------------------
#  Peek gate – auto-engage suppressor even if <fc> appears later
# ------------------------------------------------------------------
class PeekGate:
    """
    • Buffers incoming text until we are sure whether a <fc> block will
      appear in this stream.
        – If <fc> is found → engage suppressor for the rest of the stream.
        – If the buffer exceeds `peek_limit` without <fc> → give up and
          pass everything straight through (no function call expected).
    """
    def __init__(self, downstream, peek_limit: int = 2048):
        self.downstream   = downstream
        self.peek_limit   = peek_limit     # max bytes to keep while peeking
        self.buf          = ""
        self.mode         = "peeking"      # → "normal" after decision
        self.suppressing  = False          # flips when we see <fc>

    def feed(self, chunk: str) -> str:
        # Once the decision is made, just delegate.
        if self.mode == "normal":
            return (
                self.downstream.filter_chunk(chunk)
                if self.suppressing
                else chunk
            )

        # Still peeking …
        self.buf += chunk

        # Do we see the start of a function-call block yet?
        m = re.search(r"<\s*fc\s*>", self.buf, flags=re.IGNORECASE)
        if m:
            # Flush text that precedes <fc>
            head = self.buf[:m.start()]
            print("[PEEK] <fc> located after leading text – engaging suppressor.")
            self.suppressing = True
            self.mode = "normal"
            # Send head unchanged, send rest through suppressor
            tail = self.buf[m.start():]
            self.buf = ""  # clear buffer
            return head + self.downstream.filter_chunk(tail)

        # No tag yet – if buffer too big we assume there is **no** <fc>.
        if len(self.buf) >= self.peek_limit:
            print("[PEEK] no <fc> tag within first %d chars – no suppression."
                  % self.peek_limit)
            self.mode = "normal"
            self.suppressing = False
            out, self.buf = self.buf, ""
            return out

        # Still unsure → don’t emit anything yet
        return ""

# ------------------------------------------------------------------
# 1.  Tool executor  (runs locally for this demo)
# ------------------------------------------------------------------
def get_flight_times(tool_name: str, arguments: dict) -> str:
    """Fake flight-time lookup."""
    if tool_name == "get_flight_times":
        return json.dumps({
            "status":         "success",
            "departure":      arguments.get("departure"),
            "arrival":        arguments.get("arrival"),
            "duration":       "4h 30m",
            "departure_time": "10:00 AM PST",
            "arrival_time":   "06:30 PM EST"
        })
    return json.dumps({"status": "error", "message": f"unknown tool '{tool_name}'"})

# ------------------------------------------------------------------
# 2.  Thread + message + run
# ------------------------------------------------------------------
thread = client.threads.create_thread()

message = client.messages.create_message(
    thread_id=thread.id,
    role="user",
    content="Please fetch me the flight times between LAX and JFK.",
    assistant_id=ASSISTANT_ID
)

run = client.runs.create_run(
    assistant_id=ASSISTANT_ID,
    thread_id=thread.id
)

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

suppressor = FunctionCallSuppressor()
peek_gate  = PeekGate(suppressor)

for chunk in stream.stream_chunks(
        provider=PROVIDER_KW,
        model=MODEL_ID,
        timeout_per_chunk=6.0):

    # Provider-labelled function-call chunks
    if chunk.get("type") == "function_call":
        print("[SUPPRESSOR] blocked provider-labelled function_call chunk.")
        continue

    txt = chunk.get("content", "")
    if not txt:
        continue

    out = peek_gate.feed(txt)
    if out.strip():
        print(out, end="", flush=True)

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
    timeout=60.0,
    interval=0.1
)

# ------------------------------------------------------------------
# 5.  Stream final assistant reply
# ------------------------------------------------------------------
if handled:
    print("\n\n[✓] Tool executed, streaming final answer …\n")

    client.messages.create_message(
        assistant_id=ASSISTANT_ID,
        thread_id=thread.id,
        role="user",
        content="Please provide the output from the tool"
    )

    stream.setup(
        user_id=USER_ID,
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        message_id=message.id,
        run_id=run.id,
        api_key=HYPERBOLIC_API_KEY
    )

    for chunk in stream.stream_chunks(
            provider=PROVIDER_KW,
            model=MODEL_ID,
            timeout_per_chunk=30.0):

        txt = chunk.get("content", "")
        if not txt:
            continue

        out = suppressor.filter_chunk(txt)   # suppressor alone is fine now
        if out.strip():
            print(out, end="", flush=True)

    print("\n\n--- End of Stream ---")
else:
    print("\n[!] No function call detected or execution failed.")
