"""
Vector‑store quick‑start
=======================

1.  Create a store (backed by Qdrant & DB row)
2.  Verify it was created
3.  Ingest a local text file – the SDK will chunk, embed and upsert
4.  Ask a natural‑language query and print the top‑k matches
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from projectdavid import Entity
from projectdavid_common import UtilsInterface   # only for pretty logging

# --------------------------------------------------------------------- #
# environment & client
# --------------------------------------------------------------------- #
load_dotenv()                                        # reads .env in cwd

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)

log = UtilsInterface.LoggingUtility()               # optional

# --------------------------------------------------------------------- #
# 1.  Create a vector store
# --------------------------------------------------------------------- #

store = client.vectors.create_vector_store(
    name="cook‑book‑demo",

)

log.info("Created store %s (collection %s)", store.id, store.collection_name)

# --------------------------------------------------------------------- #
# 2.  Quick diagnostic (optional)
# --------------------------------------------------------------------- #
# sanity = client.vectors.retrieve_vector_store(store.id)
# log.info("Files so far: %d", sanity.file_count)     # should be 0 on first run

# --------------------------------------------------------------------- #
# 3.  Add a file (chunk → embed → upsert → register)
# --------------------------------------------------------------------- #
FILE_PATH = Path("docs/Donoghue_v_Stevenson__1932__UKHL_100__26_May_1932_.pdf")

file_rec = client.vectors.add_file_to_vector_store(
    vector_store_id=store.id,
    file_path=FILE_PATH,
)
log.info("Ingested %s (status=%s)", FILE_PATH.name, file_rec.status)

# --------------------------------------------------------------------- #
# 4.  Run a similarity search
# --------------------------------------------------------------------- #
query = "proof, and in my opinion she is entitled to have an opportunity"
hits = client.vectors.vector_file_search_raw(
    vector_store_id=store.id,
    query_text=query,
    top_k=5,
)

print("\nTop‑k results for query:\n", query)
for i, h in enumerate(hits, 1):
    print(f"{i:>2}. score={h['score']:.3f}  text={h['text'][:120]!r}")

