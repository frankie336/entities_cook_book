# ml_utils.py
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent / "ml-100k" / "ml-100k"
GENRE_FLAGS = [
    "Action", "Adventure", "Animation", "Children's", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
]

def load_movielens() -> pd.DataFrame:
    """Return MovieLens 100K metadata with genres list + nullable year."""
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
    movies["genres"] = movies.apply(
        lambda r: [g for g in GENRE_FLAGS if r[g] == 1], axis=1
    )
    movies["release_year"] = (
        pd.to_datetime(movies["release_date"], format="%d-%b-%Y", errors="coerce")
          .dt.year.astype("Int64")
    )
    return movies
