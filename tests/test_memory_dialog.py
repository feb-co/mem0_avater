from mem0.memory_dialogue.chat_memory import ChatMemory
import json
from datetime import datetime

config = {
    # "embedder": {
    #     "provider": "openai",
    #     "config": {
    #         "model": "text-embedding-3-small"
    #     }
    # },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o",
            "temperature": 0.2,
            "max_tokens": 1500,
        }
    }    
}

from mem0 import Memory
m = ChatMemory.from_config(config)

# m = Memory()

## example
if 0:
    # 1. Add: Store a memory from any unstructured text
    result = m.add("I am working on improving my tennis skills. Suggest some online courses.", user_id="alice", metadata={"category": "hobbies"})
    print(result)
    # Created memory --> 'Improving her tennis skills.' and 'Looking for online suggestions.'
    
    # 2. Get all memories
    all_memories = m.get_all(user_id="alice")

    # 3. Search: search related memories
    related_memories = m.search(query="What are Alice's hobbies?", user_id="alice")
    print(related_memories)
    # Retrieved memory --> 'Likes to play tennis on weekends'

data = json.load(open("tests/demo_data.json"))[1][:10]

user_name = "alice1"

idx = 0

while idx < len(data):
    print(idx)
    # all_memories = m.get_all(user_id="alice1")
    # sorted_data = sorted(all_memories, key=lambda x: datetime.fromisoformat(x['updated_at']))
    # import pdb; pdb.set_trace()

    item = data[idx]
    if item.get("requires_context"):
        # import pdb; pdb.set_trace()
        print(item["requires_context"])
        print(item["content"])
        related_memories = m.search(query=item["content"], user_id=user_name)
        
        for mem in related_memories: print(mem)
    message = [
        {
            'role': item["role"],
            'content': data[idx]["content"],
        },
        {
            'role': 'assistant',
            'content': data[idx+1]["content"],
        }
    ]
    m.add(message, user_id=user_name, metadata={"id": item["id"], "role": item["role"]})
    idx += 2


print("== output all context memories")
all_memories = m.get_all(user_id="alice1", agent_id="context")
for mem in all_memories:
    print(mem)
    print("-"*100)

print("-"*100)
print("== output all observation memories")
all_memories = m.get_all(user_id="alice1", agent_id="observation")
for mem in all_memories:
    print(mem['memory'])
    print("-"*100)

print("-"*100)
print("== test observation search")
# test observation search
related_memories = m.search(query="What are Alice's hobbies?", user_id="alice", agent_id="observation")
print(related_memories)

print("-"*100)
print("== test context search")
# test observation search with context
related_memories = m.search(query="What are Alice's hobbies?", user_id="alice", agent_id="context")
print(related_memories)

