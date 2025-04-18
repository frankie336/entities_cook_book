#!/usr/bin/env python3
# deprecated-upload_metadata_type2.py  (MovieLens fuzzy‑vector demo)

# vect_I1KhGs8LkHJbbNh4fuKYDQ

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from projectdavid import Entity

# ─── Setup ───────────────────────────────────────────────────────────────
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)
USER_ID = os.getenv("ENTITIES_USER_ID")

# ─── Load MovieLens metadata ─────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "ml-100k" / "ml-100k"
movies = pd.read_csv(
    DATA_DIR / "u.item",
    sep="|",
    encoding="latin-1",
    header=None,
    usecols=list(range(24)),
    names=[
        "movie_id", "title", "release_date", "video_release_date", "IMDb_URL",
        "unknown", "Action", "Adventure", "Animation", "Children's", "Comedy",
        "Crime", "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror",
        "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
    ],
)

GENRE_FLAGS = [
    "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
]

movies["genres"] = movies.apply(
    lambda r: [g for g in GENRE_FLAGS if r[g] == 1], axis=1
)

# Parse year → pandas nullable integer (Int64)
movies["release_year"] = (
    pd.to_datetime(movies["release_date"], format="%d-%b-%Y", errors="coerce")
      .dt.year
      .astype("Int64")          # keeps <NA> instead of NaN
)

# ─── 1. Create a fresh vector store ──────────────────────────────────────
vs = client.vectors.create_vector_store(
    name="movielens-fuzzy-demo",
    user_id=USER_ID,
)
collection = vs.collection_name
print(f"🆕 Created vector store {vs.id} → collection '{collection}'")

# ─── 2. Ingest each movie as one fuzzy point ─────────────────────────────
embedder = client.vectors.file_processor.embedding_model   # convenience

for _, mv in movies.iterrows():
    # — Build plain‑text description —───────────────────────────────────
    genre_str = ", ".join(mv.genres) if mv.genres else "Unknown genre"
    year_str  = f" Year: {mv.release_year}" if pd.notna(mv.release_year) else ""
    text      = f"{mv.title}. Genres: {genre_str}.{year_str}"

    # — Generate embedding —──────────────────────────────────────────────
    vec = embedder.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True,
        truncate="model_max_length",
        show_progress_bar=False,
    )[0].tolist()

    # — Metadata payload —────────────────────────────────────────────────
    meta = {
        "item_id": int(mv.movie_id),
        "title":   mv.title,
        "genres":  mv.genres,
        "release_year": (int(mv.release_year) if pd.notna(mv.release_year) else None),
    }

    # — Upsert into Qdrant —──────────────────────────────────────────────
    client.vectors.vector_manager.add_to_store(
        store_name=collection,
        texts=[text],
        vectors=[vec],
        metadata=[meta],
    )

print(f"✅ Ingested {len(movies)} movies.")

# ─── 3. Quick fuzzy‑search sanity check ──────────────────────────────────
queries = [
    "A light‑hearted animal cartoon",
    "90s romantic drama movie",
    "Classic sci‑fi before 2000",
    "Similar vibe to Jurassic Park",
    "Murder mystery thriller",
]

for q in queries:
    print(f"\n🔍 Query: {q!r}")
    qvec = embedder.encode(
        [q],
        convert_to_numpy=True,
        normalize_embeddings=True,
        truncate="model_max_length",
    )[0].tolist()

    hits = client.vectors.vector_manager.query_store(
        store_name=collection,
        query_vector=qvec,
        top_k=5,
    )

    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        genres = ", ".join(m["genres"]) if m["genres"] else "Unknown genre"
        year   = m["release_year"] or "—"
        print(f"{i}. 🎬 {m['title']} — [{genres}] ({year})  score={h['score']:.3f}")
