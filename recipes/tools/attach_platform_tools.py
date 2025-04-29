import os
from dotenv import load_dotenv
from projectdavid import Entity

load_dotenv()
client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY")
)


assistant = client.assistants.create_assistant(
    name="some_test_assistant",
    tools=[{"type": "code_interpreter"}]

)

print(assistant)

