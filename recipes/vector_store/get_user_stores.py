import os
from dotenv import load_dotenv
from projectdavid import Entity
load_dotenv()

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ADMIN_API_KEY"),
)


#------------------------------------------------------
# Create default file_search vector store for the user
#
#------------------------------------------------------
client.vectors.create_vector_store_for_user(owner_id="user_36xmJoz1ywAiuOAxYvKq2Z",
                                            name="file_search"
)






store = client.vectors.get_stores_by_user(
    _user_id="user_36xmJoz1ywAiuOAxYvKq2Z"

)




print(store)
