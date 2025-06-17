#!/usr/bin/env python3
"""
Run a set of nuanced semantic queries against an existing MovieLens
vector-store, using the **public VectorStoreClient API** instead of the
low-level VectorStoreManager.

• Relies on `vector_file_search_raw()`, which internally handles
  text-embedding, auto-detects the correct vector field, and applies any
  patched logic you’ve added to VectorStoreClient.
• `STORE_ID` must be the *backend store id* (not the collection name).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from projectdavid import Entity

# ─── configuration ──────────────────────────────────────────────────────────
load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:9000")
API_KEY  = os.getenv("ENTITIES_API_KEY")
STORE_ID = "vect_mqfWyNlZbacer73PQu4Upy"        # ← backend id, **not** collection
TOP_K    = int(os.getenv("TOP_K", "5"))

client = Entity(base_url=BASE_URL, api_key=API_KEY)

# ─── helper: single search call (uses VectorStoreClient) ────────────────────
def search(query: str, top_k: int = TOP_K) -> None:
    print(f"\n🔍  {query}")
    hits = client.vectors.vector_file_search_raw(
        vector_store_id = STORE_ID,
        query_text      = query,
        top_k           = top_k,
    )

    if not hits:
        print("🙈  No results")
        return

    for idx, h in enumerate(hits, 1):
        md      = h.get("meta_data") or h.get("metadata") or {}
        title   = md.get("title", "<untitled>")
        genres  = ", ".join(md.get("genres", [])) or "—"
        year    = md.get("release_year", "—")
        print(f"{idx}. 🎬 {title} — [{genres}] ({year})  score={h['score']:.3f}")

# ─── queries to run ─────────────────────────────────────────────────────────
QUERIES = [
    # 🎭 Stylistic & tonal
    "A film with a whimsical tone but dark undertones, likely animated and aimed at children but emotionally traumatic for adults.",
    "An ensemble comedy where at least one character wears a trench coat and the score uses saxophones.",
    "A low-budget 90s drama about unrequited love that never explicitly mentions romance.",

    # 🧠 Temporal & relational
    "A sci-fi movie made before the year 2000 that was clearly inspired by Blade Runner but takes place underwater.",
    "A musical from the 80s that probably flopped on release but became a cult classic due to VHS circulation.",
    "A romantic comedy that feels like a precursor to When Harry Met Sally, but no one remembers it by name.",

    # 🪩 Subcultural / atmospheric
    "A movie you’d find on late-night TV in 1997, featuring moody synth music, leather jackets, and an ambiguous ending.",
    "Something Gen X would consider nostalgic, but that millennials mostly know from memes.",
    "A film that feels like it should have aired on PBS but has unexpected violence.",

    # 🕵️ Meta / ironic
    "A murder mystery that’s not really about the murder, but about small-town dynamics and buried secrets.",
    "A movie pretending to be deep, made in the 90s, with at least one character who quotes Nietzsche.",
    "A self-serious sci-fi film that takes itself too seriously but accidentally becomes a comedy.",

    # 🧩 Hypothetical crossover
    "If Jurassic Park were directed by Tim Burton and scored by Danny Elfman but was set in space instead of an island.",
    "A mashup of Casablanca and The Matrix in spirit, if not in literal content.",
    "Something that feels like a live-action adaptation of a dream about Looney Tunes crossed with an arthouse thriller.",
]

if __name__ == "__main__":
    for q in QUERIES:
        search(q)
