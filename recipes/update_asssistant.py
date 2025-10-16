import os
from dotenv import load_dotenv
from projectdavid import Entity

load_dotenv()

client = Entity()


modify_assistant = client.assistants.update_assistant(
    assistant_id="asst_7PHLBJkdXqu8HF4zFzbS0w",
    name="Todd",
    description="test_case",
    model='GPT3',
    instructions="You are now a web search bot",
    tools=[{"type": "web_search"},
                   ],

)
print(modify_assistant.model_dump_json())