"""
Vector‑store quick‑start
=========================

1.  Create a store (backed by Qdrant & DB row)
2.  Verify it was created
3.  Ingest a local text file – the SDK will chunk, embed and upsert
4.  Ask a natural‑language query and print top‑k matches using a complex filter

This example demonstrates how to use metadata filters to refine your semantic search:
- `must`:    conditions that **all** matching points must satisfy
- `must_not`: conditions that **exclude** any matching points
- You can combine multiple `must`/`must_not` clauses to target only the portions
  of your data (e.g. a specific file, a range of chunk indices, etc.)
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from projectdavid import Entity
from projectdavid_common import UtilsInterface  # for logging

# --------------------------------------------------------------------- #
# Environment setup
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
    name="cook‑book‑demo",

)
log.info("Created store %s (collection %s)", store.id, store.collection_name)

# --------------------------------------------------------------------- #
# 2. Confirm creation (sanity check)
# --------------------------------------------------------------------- #
# diagnostic = client.vectors.retrieve_vector_store(store.id)
# log.info("Files so far: %d", diagnostic.file_count)   # Expect 0 on first run

# --------------------------------------------------------------------- #
# 3. Add a file (embed → upsert → register)
# --------------------------------------------------------------------- #
FILE_PATH = Path("201101_donoghue_v-_stevenson.txt")
file_entry = client.vectors.add_file_to_vector_store(
    vector_store_id=store.id,
    file_path=FILE_PATH,
)
log.info("Ingested file: %s (status=%s)", file_entry.file_name, file_entry.status)

# --------------------------------------------------------------------- #
# 4. Complex semantic search using metadata filters
# --------------------------------------------------------------------- #
# Define a natural‑language query
query = "duty of care and reparation"

# Build a complex filter:
#  - only include chunks from our specific file
#  - restrict to chunk indices between 100 and 300
#  - exclude any chunks with index >= 250 (e.g. too far down in the document)
filters = {
    "must": [
        {
            "key": "metadata.file_name",
            "match": {"value": FILE_PATH.name}
        },
        {
            "key": "metadata.chunk_index",
            "range": {"gte": 100, "lte": 300}
        }
    ],
    "must_not": [
        {
            "key": "metadata.chunk_index",
            "range": {"gte": 250}
        }
    ]
}

# Execute the search with top_k=5 results
results = client.vectors.search_vector_store(
    vector_store_id=store.id,
    query_text=query,
    top_k=5,
    filters=filters,
)

# Display results
print(f"\nTop‑k results for query:\n'{query}'\n")
for i, res in enumerate(results, 1):
    chunk_idx = res["metadata"].get("chunk_index")
    snippet = res["text"][:120].replace("\n", " ")
    print(f"{i:>2}. score={res['score']:.3f}  chunk_index={chunk_idx}  text='{snippet}…'")
