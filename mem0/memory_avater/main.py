
import json
import logging
import concurrent
import warnings
from copy import deepcopy
from pydantic import ValidationError
from typing import Any, Dict

from mem0.configs.base import MemoryConfig, MemoryItem
from mem0.configs.prompts import get_update_memory_messages

from mem0.memory.main import Memory
from mem0.memory.telemetry import capture_event
from mem0.memory.utils import get_fact_retrieval_messages, parse_messages
from mem0.memory.storage import SQLiteManager

from mem0.utils.factory import EmbedderFactory, LlmFactory, VectorStoreFactory

from mem0.memory_avater.memory_base_worker import MemoryBaseWorker
from mem0.memory_avater.prompt_context_explain import CONTEXT_EXPLAIN_PROMPT


logger = logging.getLogger(__name__)


class AvaterMemory(Memory):
    def __init__(self, config: MemoryConfig = MemoryConfig()):
        
        if not hasattr(config, 'version'):
            print("Warning: config missing version field")
            config.version = 'v1.0'
            
        super().__init__(config)
        
        if not hasattr(self, 'api_version'):
            self.api_version = self.config.version
        
        self.memory_base_worker = MemoryBaseWorker(config)

    def parse_messages_session(self, messages):
        if isinstance(messages, str):
            return [messages]
        
        if isinstance(messages, list):
            sessions = []
            current_session = ""
            
            for i in range(len(messages)):
                msg = messages[i]
                
                if msg["role"] == "user":
                    current_session += f"user: {msg['content']}\n"
                    
                    # Look ahead for assistant's response
                    if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                        current_session += f"assistant: {messages[i + 1]['content']}\n"
                        
                    sessions.append(current_session.strip())
                    current_session = ""
            return sessions
        return []

    def add(
        self,
        messages,
        user_id=None,
        agent_id=None,
        run_id=None,
        metadata=None,
        filters=None,
        prompt=None,
    ):
        """
        Create a new memory.

        Args:
            messages (str or List[Dict[str, str]]): Messages to store in the memory.
            user_id (str, optional): ID of the user creating the memory. Defaults to None.
            agent_id (str, optional): ID of the agent creating the memory. Defaults to None.
            run_id (str, optional): ID of the run creating the memory. Defaults to None.
            metadata (dict, optional): Metadata to store with the memory. Defaults to None.
            filters (dict, optional): Filters to apply to the search. Defaults to None.
            prompt (str, optional): Prompt to use for memory deduction. Defaults to None.

        Returns:
            dict: A dictionary containing the result of the memory addition operation.
            result: dict of affected events with each dict has the following key:
              'memories': affected memories
              'graph': affected graph memories

              'memories' and 'graph' is a dict, each with following subkeys:
                'add': added memory
                'update': updated memory
                'delete': deleted memory


        """
        if metadata is None:
            metadata = {}

        filters = filters or {}
        if user_id:
            filters["user_id"] = metadata["user_id"] = user_id
        if agent_id:
            filters["agent_id"] = metadata["agent_id"] = agent_id
        if run_id:
            filters["run_id"] = metadata["run_id"] = run_id

        if not any(key in filters for key in ("user_id", "agent_id", "run_id")):
            raise ValueError("One of the filters: user_id, agent_id or run_id is required!")

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(self._add_to_vector_store, messages, metadata, filters)
            future2 = executor.submit(self._add_to_graph, messages, filters)

            concurrent.futures.wait([future1, future2])

            vector_store_result = future1.result()
            graph_result = future2.result()

        if self.api_version == "v1.1":
            return {
                "results": vector_store_result,
                "relations": graph_result,
            }
        else:
            warnings.warn(
                "The current add API output format is deprecated. "
                "To use the latest format, set `api_version='v1.1'`. "
                "The current format will be removed in mem0ai 1.1.0 and later versions.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return vector_store_result
    
    def get_context_explanation(self, messages, metadata):
        if not any(key in metadata for key in ("user_id", "agent_id", "run_id")):
            return messages
        
        document_context = self.get_all(
            user_id  = metadata.get("user_id", None), 
            agent_id = metadata.get("agent_id", None), 
            run_id   = metadata.get("run_id", None)
        )
        if not document_context:
            return messages
        
        from datetime import datetime
        document_context = sorted(document_context, key=lambda x: datetime.fromisoformat(x['updated_at']))
        document_context = "\n".join([f"<session {i+1}>\n{mem['memory']}\n</session {i+1}>\n" for i, mem in enumerate(document_context[:20])])
        
        print(document_context)
        
        out_messages = []
        for msg in messages:
            context_explain_prompt = CONTEXT_EXPLAIN_PROMPT.format(WHOLE_DOCUMENT=document_context, CHUNK_CONTENT=msg)
            context_explain_response = self.llm.generate_response(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": context_explain_prompt}
                ],
            )
            out_messages.append(msg + "\n" + f"chunk explanation:\n{context_explain_response}")
        return out_messages

    def _add_to_vector_store(self, messages, metadata, filters, context_explain=True):
        metadata['agent_id'] = 'context'
        self._add_observation_to_vector_store(messages, deepcopy(metadata), filters)

        parsed_messages = self.parse_messages_session(messages)
        print(parsed_messages)
        if context_explain:
            parsed_messages = self.get_context_explanation(parsed_messages, metadata)
        
        returned_memories = []
        
        for msg_session in parsed_messages:
            try:
                memory_id = self._create_memory(
                    data=msg_session, existing_embeddings={}, metadata=metadata
                )
                returned_memories.append(
                    {
                        "id": memory_id,
                        "memory": msg_session,
                        "event": "ADD",
                    }
                )
            except Exception as e:
                logging.error(f"Error in new_memories_with_actions: {e}")

        capture_event("mem0.add", self, {"version": self.api_version, "keys": list(filters.keys())})

        return returned_memories


    def _add_observation_to_vector_store(self, messages, metadata, filters):
        metadata['agent_id'] = 'observation'
        
        new_retrieved_obs = self.memory_base_worker.get_observation(messages, metadata)

        retrieved_old_memory = []
        new_message_embeddings = {}
        for new_mem in new_retrieved_obs:
            messages_embeddings = self.embedding_model.embed(new_mem)
            new_message_embeddings[new_mem] = messages_embeddings
            existing_memories = self.vector_store.search(
                query=messages_embeddings,
                limit=5,
                filters=filters,
            )
            for mem in existing_memories:
                retrieved_old_memory.append({"id": mem.id, "text": mem.payload["data"]})

        logging.info(f"Total existing memories: {len(retrieved_old_memory)}")

        # mapping UUIDs with integers for handling UUID hallucinations
        temp_uuid_mapping = {}
        for idx, item in enumerate(retrieved_old_memory):
            temp_uuid_mapping[str(idx)] = item["id"]
            retrieved_old_memory[idx]["id"] = str(idx)

        function_calling_prompt = get_update_memory_messages(retrieved_old_memory, new_retrieved_obs)

        new_memories_with_actions = self.llm.generate_response(
            messages=[{"role": "user", "content": function_calling_prompt}],
            response_format={"type": "json_object"},
        )
        new_memories_with_actions = json.loads(new_memories_with_actions)

        returned_memories = []
        try:
            for resp in new_memories_with_actions["memory"]:
                logging.info(resp)
                try:
                    if resp["event"] == "ADD":
                        memory_id = self._create_memory(
                            data=resp["text"], existing_embeddings=new_message_embeddings, metadata=metadata
                        )
                        returned_memories.append(
                            {
                                "id": memory_id,
                                "memory": resp["text"],
                                "event": resp["event"],
                            }
                        )
                    elif resp["event"] == "UPDATE":
                        self._update_memory(
                            memory_id=temp_uuid_mapping[resp["id"]],
                            data=resp["text"],
                            existing_embeddings=new_message_embeddings,
                            metadata=metadata,
                        )
                        returned_memories.append(
                            {
                                "id": temp_uuid_mapping[resp["id"]],
                                "memory": resp["text"],
                                "event": resp["event"],
                                "previous_memory": resp["old_memory"],
                            }
                        )
                    elif resp["event"] == "DELETE":
                        self._delete_memory(memory_id=temp_uuid_mapping[resp["id"]])
                        returned_memories.append(
                            {
                                "id": temp_uuid_mapping[resp["id"]],
                                "memory": resp["text"],
                                "event": resp["event"],
                            }
                        )
                    elif resp["event"] == "NONE":
                        logging.info("NOOP for Memory.")
                except Exception as e:
                    logging.error(f"Error in new_memories_with_actions: {e}")
        except Exception as e:
            logging.error(f"Error in new_memories_with_actions: {e}")

        capture_event("mem0.add", self, {"version": self.api_version, "keys": list(filters.keys())})

        return returned_memories    