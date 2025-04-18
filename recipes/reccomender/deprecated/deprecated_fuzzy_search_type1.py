import os
from dotenv import load_dotenv
from projectdavid import Entity
from projectdavid_common import UtilsInterface

# ─── Load .env Config ─────────────────────────────────────────────────────────
load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)
log = UtilsInterface.LoggingUtility()

# ─── Target vector store ──────────────────────────────────────────────────────
VECTOR_STORE_ID = "vect_lP4CCazOET1LdolupNx36G"

# ─── Define fuzzy / natural-language queries ──────────────────────────────────
queries = [
    "Find me a light-hearted cartoon with animals",
    "Romantic movies from the 90s with emotional drama",
    "Sci-fi or space thrillers made before the 2000s",
    "Movies similar in theme to Jurassic Park",
    "Something with mystery and murder",
]

# ─── Execute searches ─────────────────────────────────────────────────────────
for query in queries:
    log.info(f"🔍 Query: {query}")
    results = client.vectors.search_vector_store(
        vector_store_id=VECTOR_STORE_ID,
        query_text=query,
        top_k=5,  # return top 5 matches
    )
    print(f"\n🟢 Results for: {query}")
    for i, hit in enumerate(results, 1):
        title = hit["metadata"].get("title", "N/A")
        genres = ", ".join(hit["metadata"].get("genres", []))
        score = hit["score"]
        print(f"{i}. 🎬 {title} — [{genres}] (score={score:.3f})")
