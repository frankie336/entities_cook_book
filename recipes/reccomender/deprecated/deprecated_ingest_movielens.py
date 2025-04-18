#!/usr/bin/env python3
"""
Ingest MovieLens items into a fresh vector store.

Usage:
    python deprecated_ingest_movielens.py --name movielens-fuzzy-demo
"""
import argparse, os
from dotenv import load_dotenv
from projectdavid import Entity
from ml_utils import load_movielens

load_dotenv()

def main(store_name: str):
    client = Entity(
        base_url=os.getenv("BASE_URL", "http://localhost:9000"),
        api_key=os.getenv("ENTITIES_API_KEY"),
    )
    user_id = os.getenv("ENTITIES_USER_ID")

    movies = load_movielens()
    vs = client.vectors.create_vector_store(name=store_name, user_id=user_id)
    collection = vs.collection_name
    embedder = client.vectors.file_processor.embedding_model

    for _, mv in movies.iterrows():
        text = (
            f"{mv.title}. Genres: {', '.join(mv.genres) or 'Unknown genre'}."
            f"{f' Year: {mv.release_year}' if mv.release_year.notna() else ''}"
        )
        vec = embedder.encode(
            [text], convert_to_numpy=True, normalize_embeddings=True,
            truncate="model_max_length", show_progress_bar=False
        )[0].tolist()
        meta = {
            "item_id": int(mv.movie_id),
            "title": mv.title,
            "genres": mv.genres,
            "release_year": int(mv.release_year) if mv.release_year.notna() else None,
        }
        client.vectors.vector_manager.add_to_store(
            store_name=collection, texts=[text], vectors=[vec], metadata=[meta]
        )

    print(f"✅ Ingested {len(movies)} movies into {collection}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="movielens-fuzzy-demo",
                   help="Human‑readable vector‑store name")
    main(**vars(p.parse_args()))
