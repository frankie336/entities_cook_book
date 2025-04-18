#!/usr/bin/env python3
"""
Ingest MovieLens metadata into a vector store,
embedding all known descriptive attributes into vectorized text.

vect_wHvnnr27MGNCVIhz9yqg07

"""

import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from projectdavid import Entity

# ─── Load environment and init SDK ────────────────────────────────────────────
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)
USER_ID = os.getenv("ENTITIES_USER_ID")

# ─── Load MovieLens 100k metadata ─────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "ml-100k" / "ml-100k"
GENRE_FLAGS = [
    "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
]

movies = pd.read_csv(
    DATA_DIR / "u.item",
    sep="|",
    encoding="latin-1",
    header=None,
    usecols=list(range(24)),
    names=[
        "movie_id", "title", "release_date", "video_release_date", "IMDb_URL",
        "unknown", *GENRE_FLAGS
    ],
)

# Process genres
movies["genres"] = movies.apply(
    lambda row: [g for g in GENRE_FLAGS if row[g] == 1], axis=1
)

# Process dates
movies["release_year"] = (
    pd.to_datetime(movies["release_date"], format="%d-%b-%Y", errors="coerce")
      .dt.year.astype("Int64")
)

# ─── Full text embedding construction ─────────────────────────────────────────
def build_embedding_text(mv: pd.Series) -> str:
    fields = [f"Title: {mv.title}"]

    if mv.genres:
        fields.append(f"Genres: {', '.join(mv.genres)}")

    if pd.notna(mv.release_year):
        fields.append(f"Released in {int(mv.release_year)}")

    if isinstance(mv.release_date, str) and mv.release_date.strip():
        fields.append(f"Release date: {mv.release_date}")

    if isinstance(mv.video_release_date, str) and mv.video_release_date.strip():
        fields.append(f"Video release: {mv.video_release_date}")

    if isinstance(mv.IMDb_URL, str) and mv.IMDb_URL.startswith("http"):
        fields.append(f"IMDb: {mv.IMDb_URL}")

    return ". ".join(fields) + "."

# ─── Create vector store ──────────────────────────────────────────────────────
vs = client.vectors.create_vector_store(
    name="movielens-complete-demo",
    user_id=USER_ID,
)
collection = vs.collection_name
print(f"🆕 Created vector store {vs.id} → collection '{collection}'")

# ─── Embed & ingest ──────────────────────────────────────────────────────────
embedder = client.vectors.file_processor.embedding_model

for _, mv in movies.iterrows():
    text = build_embedding_text(mv)
    vec = embedder.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True,
        truncate="model_max_length",
        show_progress_bar=False,
    )[0].tolist()

    meta = {
        "item_id": int(mv.movie_id),
        "title": mv.title,
        "genres": mv.genres,
        "release_year": int(mv.release_year) if pd.notna(mv.release_year) else None,
        "release_date": mv.release_date,
        "video_release_date": mv.video_release_date,
        "IMDb_URL": mv.IMDb_URL,
    }

    client.vectors.vector_manager.add_to_store(
        store_name=collection,
        texts=[text],
        vectors=[vec],
        metadata=[meta],
    )

print(f"✅ Ingested {len(movies)} fully enriched movies.")
