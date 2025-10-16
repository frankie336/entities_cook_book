from dotenv import load_dotenv

load_dotenv()

from projectdavid import Entity

client = Entity()

thread = client.threads.create_thread()
print(thread.model_dump_json())

message = client.messages.create_message(
        thread_id=thread.id,
        role="user",
        content="Explain a black hole to me in pure mathematical terms",
        assistant_id="asst_5X2dIbKJsm8IgQTOAvK5WI",
    )


print(message.model_dump_json())


run = client.runs.create_run(thread_id=thread.id,
                             assistant_id="",

                             )

print(run.model_dump_json())