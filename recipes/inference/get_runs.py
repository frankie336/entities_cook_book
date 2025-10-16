import os
from dotenv import load_dotenv
from projectdavid import Entity
from projectdavid.synthesis.retriever import retrieve

# Load environment variables from .env
load_dotenv()
print(os.getenv("ENTITIES_API_KEY"))

# ── Initialize the SDK client ────────────────────────────────────────────

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY")
)

# retrieve_run = client.runs.retrieve_run(run_id="run_uhvbHTlQhUdVIc3VQ58Ioy")
# print(retrieve_run.model_dump_json())


update_run = client.runs.update_run(
    run_id="run_uhvbHTlQhUdVIc3VQ58Ioy",
    metadata= {"stage": "ingest", "attempt": 1}
)
print(update_run.model_dump_json())



cancel_run = client.runs.cancel_run(run_id="run_uhvbHTlQhUdVIc3VQ58Ioy")
print(cancel_run)