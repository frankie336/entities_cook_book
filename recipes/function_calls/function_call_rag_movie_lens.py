"""
Movie‑Lens RAG  ⟶  Function‑Call Demo
-------------------------------------
ASSUMPTIONS
• Your vector store **already exists** and is fully populated.
• Assistant “movie‑assistant” is configured with a `search_movies` tool
  whose JSON schema matches the arguments used below.
• The script demonstrates a single round‑trip:
    1) User asks a nuanced question.
    2) LLM picks `search_movies`.
    3) Local `search_movies` executor queries Qdrant and returns JSON.
    4) Assistant streams a final, natural‑language answer.

Replace the constants (ASSISTANT_ID, MOVIE_STORE_ID, MODEL_ID) if needed.
"""
import json
import os
from dotenv import load_dotenv
from projectdavid import Entity

# ─── Env & SDK ───────────────────────────────────────────────────────────────
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)

USER_ID        = os.getenv("ENTITIES_USER_ID")                     # e.g. user_abc
ASSISTANT_ID   = "default"                                 # pre‑built
MOVIE_STORE_ID = "vect_wHvnnr27MGNCVIhz9yqg07"                     # existing store
MODEL_ID       = "hyperbolic/deepseek-ai/DeepSeek-V3-0324"
PROVIDER_KW    = "TogetherAI"
TOGETHER_KEY   = os.getenv("HYPERBOLIC_API_KEY")

# ─── Tool executor (local mock) ──────────────────────────────────────────────
def search_movies(tool_name: str, arguments: dict) -> str:
    if tool_name != "search_movies":
        return json.dumps({"status": "error", "message": f"unknown tool '{tool_name}'"})

    query = arguments.get("query", "")
    top_k = int(arguments.get("top_k", 5))
    store = arguments.get("store_id", MOVIE_STORE_ID)

    embedder = client.vectors.file_processor.embedding_model
    qvec = embedder.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        truncate="model_max_length",
    )[0].tolist()

    hits = client.vectors.vector_manager.query_store(
        store_name=store,
        query_vector=qvec,
        top_k=top_k,
    )

    results = [
        {
            "rank": i + 1,
            "title": h["metadata"]["title"],
            "genres": h["metadata"]["genres"],
            "year": h["metadata"]["release_year"],
            "score": round(h["score"], 3),
        }
        for i, h in enumerate(hits)
    ]

    # final_results = def some_pretrained_model(input='results')
    #------------------------------------------------------------
    # Deal with your user specific pretrained model results here
    # by passing the results as input. This will add some delay
    # The result is that the  final output is tailored to whatever
    # logic is contained in your pretrained model. For example,
    # It might refine and rank the list of movies  according to user
    # preferences and watch history. You will have to tailor and map
    # results according to whatever your pretrained model does
    #-------------------------------------------------------------
    # return return json.dumps({"status": "success", "results": final_results})
    return json.dumps({"status": "success", "results": results})



# ─── Thread + message + run ──────────────────────────────────────────────────
thread = client.threads.create_thread(participant_ids=[USER_ID])
message = client.messages.create_message(
    thread_id=thread.id,
    role="user",
    content="Recommend a space‑age dinosaur movie that feels like Jurassic Park.",
    assistant_id=ASSISTANT_ID,
)
run = client.runs.create_run(assistant_id=ASSISTANT_ID, thread_id=thread.id)

# ─── Stream initial assistant output (should contain the function call) ─────
stream = client.synchronous_inference_stream
stream.setup(
    user_id=USER_ID,
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID,
    message_id=message.id,
    run_id=run.id,
    api_key=TOGETHER_KEY,
)

print("\n[▶] LLM streaming (expect function call) …\n")
for chunk in stream.stream_chunks(
    provider=PROVIDER_KW, model=MODEL_ID, timeout_per_chunk=30.0
):
    if chunk.get("type") == "function_call":
        print(f"\n[function_call] → {chunk['name']}({chunk['arguments']})\n")
    else:
        print(chunk.get("content", ""), end="", flush=True)

# ─── Execute tool & feed result back ─────────────────────────────────────────
handled = client.runs.poll_and_execute_action(
    run_id=run.id,
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID,
    tool_executor=search_movies,
    actions_client=client.actions,
    messages_client=client.messages,
    timeout=10.0,
    interval=1.0,
)

# ─── Stream the assistant’s final answer ─────────────────────────────────────
if handled:
    print("\n\n[✓] Tool executed, streaming final answer …\n")

    stream.setup(
        user_id=USER_ID,
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        message_id="regenerated",
        run_id=run.id,
        api_key=TOGETHER_KEY,
    )

    for chunk in stream.stream_chunks(
        provider=PROVIDER_KW, model=MODEL_ID, timeout_per_chunk=30.0
    ):
        print(chunk.get("content", ""), end="", flush=True)

    print("\n\n--- End of Stream ---")
else:
    print("\n[!] No function call detected or execution failed.")
