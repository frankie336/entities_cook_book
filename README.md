#  Entities Cookbook

Welcome to the **Entities Cookbook** – a script-based collection of advanced examples, demos, and operational recipes for using the `projectdavid` SDK with real assistants, function calls, inference models, and vector stores.

This cookbook is optimized for:
- **Developers** looking to rapidly integrate the Entities platform
- **Power users** who want to prototype ideas with real-world patterns
- **System architects** interested in exploring modular, scalable AI assistant flows

---

## 🚀 Quickstart

### 🔧 Requirements

- Python 3.10 or newer
- Virtualenv (optional but recommended)
- `.env` file containing:

```dotenv
  ENTITIES_API_KEY=your_user_api_key
  HYPERBOLIC_API_KEY=your_streaming_api_key
  BASE_URL=http://localhost:9000
```

# 🗂 Table of Contents

<details>
<summary><strong>📦 function_calls</strong></summary>

- [`create_function_call.py`](recipes/function_calls/create_function_call.py) – _Creates a callable LLM function._
- [`attach_tool_to_existing_assistant.py`](recipes/function_calls/attach_tool_to_existing_assistant.py) – _Registers a tool to an existing assistant._
- [`basic_function_call_handling.py`](recipes/function_calls/basic_function_call_handling.py) – _Triggers, executes, and streams a function tool round‑trip using TogetherAI._

</details>

<details>
<summary><strong>🧠 inference</strong></summary>

- [`basic_completion.py`](recipes/inference/basic_completion.py) – _Basic completion using assistant streaming._

</details>

<details>
<summary><strong>🎬 RAG / MovieLens</strong></summary>

- [`ingest_movielens_all_attributes.py`](recipes/reccomender/ingest_movielens_all_attributes.py) – _Ingests and embeds all descriptive MovieLens metadata into a vector store._
- [`search_movielens.py`](recipes/reccomender/search_movielens.py) – _Command-line fuzzy vector search over MovieLens using semantic embeddings._
- [`batch_search_movielens.py`](recipes/reccomender/batch_search_movielens.py) – _Runs multiple stylistically rich semantic queries against a MovieLens vector store._
- [`register_search_movies_tool.py`](recipes/function_calls/register_search_movies_tool.py) – _Registers and attaches the `search_movies` tool for semantic MovieLens queries._
- [`function_call_rag_movie_lens.py`](recipes/function_calls/function_call_rag_movie_lens.py) – _Streams assistant replies from MovieLens-powered RAG tool calling._

</details>
