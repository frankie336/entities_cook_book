#!/usr/bin/env python3
# Run multiple nuanced semantic queries against your existing vector store

import os
from dotenv import load_dotenv
from projectdavid import Entity

# ─── Configuration ───────────────────────────────────────────────────────────
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)
store_name = "vect_wHvnnr27MGNCVIhz9yqg07"
embedder = client.vectors.file_processor.embedding_model


def search(q: str, top_k: int = 5):
    print(f"\n🔍 Query: {q}")
    qvec = embedder.encode(
        [q], convert_to_numpy=True, normalize_embeddings=True,
        truncate="model_max_length"
    )[0].tolist()
    hits = client.vectors.vector_manager.query_store(
        store_name=store_name,
        query_vector=qvec,
        top_k=top_k
    )
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        title = m["title"]
        genres = ", ".join(m["genres"]) if m["genres"] else "—"
        year = m["release_year"] or "—"
        print(f"{i}. 🎬 {title} — [{genres}] ({year}) score={h['score']:.3f}")


# ─── Nuanced queries ─────────────────────────────────────────────────────────

queries = [
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

for query in queries:
    search(query)
