"""
MovieLens vector‑store ingestion demo
=====================================

Created store vect_lP4CCazOET1LdolupNx36G

1.  Read the classic 100k movie metadata dataset
2.  Create a vector store
3.  Treat each movie as a “document” and store its title with genre metadata
"""

import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from projectdavid import Entity

# ─── Setup ────────────────────────────────────────────────────────────────────
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)
USER_ID = os.getenv("ENTITIES_USER_ID")

# ─── Read MovieLens 100k ───────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "ml-100k" / "ml-100k"

movies = pd.read_csv(
    DATA_DIR / "u.item",
    sep="|",
    encoding="latin-1",
    header=None,
    usecols=list(range(0, 24)),
    names=[
        "movie_id","title","release_date","video_release_date","IMDb_URL",
        "unknown","Action","Adventure","Animation","Children's","Comedy","Crime",
        "Documentary","Drama","Fantasy","Film-Noir","Horror","Musical","Mystery",
        "Romance","Sci-Fi","Thriller","War","Western"
    ],
)

def extract_genres(row):
    return [g for g in [
        "Action","Adventure","Animation","Children's","Comedy","Crime",
        "Documentary","Drama","Fantasy","Film-Noir","Horror","Musical",
        "Mystery","Romance","Sci-Fi","Thriller","War","Western"
    ] if row[g] == 1]

movies["genres"] = movies.apply(extract_genres, axis=1)
movies["release_year"] = pd.to_datetime(
    movies["release_date"], format="%d-%b-%Y", errors="coerce"
).dt.year

print("Sample movies:")
print(movies.head())

# ─── Create Vector Store ──────────────────────────────────────────────────────
store = client.vectors.create_vector_store(
    name="movielens-demo",
    user_id=USER_ID,
)
print(f"Created store {store.id}")

# ─── Use dummy file path and store as metadata‑only point ─────────────────────
DUMMY_PATH = SCRIPT_DIR / "placeholder.txt"  # must exist
DUMMY_PATH.touch(exist_ok=True)

for _, mv in movies.iterrows():
    client.vectors.add_file_to_vector_store(
        vector_store_id=store.id,
        file_path=DUMMY_PATH,
        user_metadata={
            "item_id": mv.movie_id,
            "title": mv.title,
            "genres": mv.genres,
            "release_year": int(mv.release_year) if not pd.isna(mv.release_year) else None,
        },
    )

print("Ingestion complete.")
