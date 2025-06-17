
from __future__ import annotations

import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv
from projectdavid import Entity



load_dotenv()

# ────────────────────────────────────────────────────────────────
#  Config – tweak here or via ENV
# ────────────────────────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "http://localhost:9000")
API_KEY = os.getenv("ENTITIES_API_KEY")
STORE_ID = "vect_mqfWyNlZbacer73PQu4Upy"
TOP_K = int(os.getenv("TOP_K", "5"))

if not STORE_ID:
    print("❌  MOVIELENS_STORE_ID env var missing – add it to .env or the IDE run‑config", file=sys.stderr)
    sys.exit(1)

# ────────────────────────────────────────────────────────────────
#  Core lookup helper (re‑uses the high‑level client search)
# ────────────────────────────────────────────────────────────────

def search_once(query: str, top_k: int = TOP_K, *, host_override: Optional[str] = None) -> None:
    """Print `top_k` matches for `query`."""

    client = Entity(base_url=BASE_URL, api_key=API_KEY)

    hits = client.vectors.vector_file_search_raw(
        vector_store_id=STORE_ID,
        query_text=query,
        top_k=top_k,

    )


    if not hits:
        print("🙈  No results\n")
        return

    for i, h in enumerate(hits, 1):
        md = h.get("meta_data") or h.get("metadata") or {}
        genres = ", ".join(md.get("genres", [])) or "Unknown genre"
        title = md.get("title", "<untitled>")
        year = md.get("release_year", "—")
        print(f"{i}. 🎬 {title} — [{genres}] ({year})  score={h['score']:.3f}")
    print()


# ────────────────────────────────────────────────────────────────
#  Entry‑point – simple REPL
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("MovieLens fuzzy search (Ctrl‑D / Ctrl‑C to exit)\n")
    try:
        while True:
            query = input("🔍 > ").strip()
            if not query:
                continue
            search_once(query)
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        sys.exit(0)
