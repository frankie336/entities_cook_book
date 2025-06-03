"""
Vector‑store quick‑start
=======================

1.  Create a store (backed by Qdrant & DB row)
2.  Verify it was created
3.  Ingest a local text file – the SDK will chunk, embed and upsert
4.  Ask a natural‑language query and print the top‑k matches
"""
import os
import time
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
    api_key=os.getenv("ADMIN_API_KEY"),
)


log = UtilsInterface.LoggingUtility()               # optional

# --------------------------------------------------------------------- #
# 1.  Create a vector store
# --------------------------------------------------------------------- #
store = client.vectors.create_vector_store(
    name="cookbookdemo",

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
FILE_PATH = Path("gym_people_watching.pdf")   # any local text file

file_rec = client.vectors.add_file_to_vector_store(
    vector_store_id=store.id,
    file_path=FILE_PATH,
)

log.info("Ingested %s (status=%s)", FILE_PATH.name, file_rec.status)

# --------------------------------------------------------------------- #
# 4.  Run a similarity search
# --------------------------------------------------------------------- #

env = client.vectors.unattended_file_search(
    vector_store_id=store.id,
    query_text="Who is the most insideous type of gym person, and why?",
)

import json, pprint
pprint.pp(json.dumps(env, indent=2))

