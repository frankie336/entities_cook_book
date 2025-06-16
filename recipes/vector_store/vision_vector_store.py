import os
from dotenv import load_dotenv
from projectdavid import Entity
load_dotenv()

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ADMIN_API_KEY"),
)


# --------------------------------------------------------------------- #
# 1.  Create a vector store
# --------------------------------------------------------------------- #
store = client.vectors.create_vector_store(
    name="cook‑book‑demo",
)

user_vision_store = client.vectors.create_vector_vision_store_for_user(
    owner_id=os.getenv("ENTITIES_USER_ID"),
    name='vision'
)

print(user_vision_store)