import os
from dotenv import load_dotenv
from projectdavid import Entity

load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY")
)

# -----------------------------------------
# Create vector store
#------------------------------------------
store = client.vectors.create_vector_store(
    name="test_vectors",

)
print(store)
# -----------------------------------------------
# create an assistant with file search turned on
#------------------------------------------------
assistant = client.assistants.create_assistant(
    name="some_test_assistant",

    tools=[{
        "type": "file_search",
        "vector_store_ids": [store.id]
    }]

)
print(assistant)

vectors  = client.vectors.get_vector_stores_for_assistant(assistant_id=assistant.id)
print(vectors)