"""
Vector‑store temporal‑search demo
=================================

1.  Create a store
2.  Ingest a file *with* a timestamp in the metadata
3.  Run a semantic search limited to chunks ingested between two ISO‑8601 datetimes
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from projectdavid import Entity
from projectdavid_common import UtilsInterface

# --------------------------------------------------------------------- #
# 0. Setup
# --------------------------------------------------------------------- #
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)
log = UtilsInterface.LoggingUtility()

# --------------------------------------------------------------------- #
# 1. Create a vector store
# --------------------------------------------------------------------- #
store = client.vectors.create_vector_store(
    name="temporal-demo",
    user_id=os.getenv("ENTITIES_USER_ID"),
)
log.info("Store %s ready (collection %s)", store.id, store.collection_name)

# --------------------------------------------------------------------- #
# 2. Ingest a file *with* an `ingested_at` timestamp
# --------------------------------------------------------------------- #
FILE_PATH = Path("my_document.txt")
ingest_time = datetime.utcnow().isoformat()
file_entry = client.vectors.add_file_to_vector_store(
    vector_store_id=store.id,
    file_path=FILE_PATH,
    user_metadata={"ingested_at": ingest_time},
)
log.info("Ingested at %s → status=%s", ingest_time, file_entry.status)

# --------------------------------------------------------------------- #
# 3. Do a temporal‑bounded search
# --------------------------------------------------------------------- #
query = "key point about liability"
# Only include chunks that were ingested in the last hour
now = datetime.utcnow()
one_hour_ago = (now - timedelta(hours=1)).isoformat()
filters = {
    "must": [
        {
            "key": "metadata.ingested_at",
            "range": {
                "gte": one_hour_ago,
                "lte": now.isoformat()
            }
        }
    ]
}

results = client.vectors.search_vector_store(
    vector_store_id=store.id,
    query_text=query,
    top_k=5,
    filters=filters,
)

print(f"\nResults for '{query}' ingested between {one_hour_ago} and {now.isoformat()}:\n")
for i, hit in enumerate(results, 1):
    t = hit["metadata"].get("ingested_at")
    print(f"{i}. score={hit['score']:.3f}  ingested_at={t}  text={hit['text'][:80]!r}")
