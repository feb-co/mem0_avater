from mem0 import Memory

import re
import json
import logging

from pydantic import ValidationError

from typing import Any, Dict

from mem0.configs.base import MemoryConfig, MemoryItem
from mem0.configs.prompts import get_update_memory_messages
from mem0.memory.telemetry import capture_event
from mem0.memory.utils import get_fact_retrieval_messages, parse_messages
from mem0.utils.factory import EmbedderFactory, LlmFactory, VectorStoreFactory
from mem0.memory.storage import SQLiteManager
from mem0.memory_dialogue.prompt_observation import OBSERVATION_RETRIEVAL_PROMPT, OBSERVATION_FEWSHOT_PROMPT


class MemoryBaseWorker:
    def __init__(self, config: MemoryConfig = MemoryConfig()):
        self.config = config

        self.custom_prompt = self.config.custom_prompt
        self.llm = LlmFactory.create(self.config.llm.provider, self.config.llm.config)
        
        self.PATTERN_V1 = re.compile(r"<(.*?)>")
        
    def parse_messages(self, messages):
        response = ""
        for msg in messages:
            if msg["role"] == "user":
                response += f"user: {msg['content']}\n"
        return response


    def get_observation(self, messages, metadata):
        metadata = metadata or {}
        
        parsed_message = self.parse_messages(messages)

        def get_observation_prompts():
            user_name = metadata.get("user_id", "USER").rstrip("_observation")
            
            prompt_list = [
                OBSERVATION_RETRIEVAL_PROMPT.format(user_name=user_name, num_obs=5),
                OBSERVATION_FEWSHOT_PROMPT.format(user_name=user_name),
            ]
            
            return '\n\n'.join(prompt_list), f"Input: {parsed_message}"

        if self.custom_prompt:
            system_prompt = self.custom_prompt
            user_prompt = f"Input: {parsed_message}"
        else:
            system_prompt, user_prompt = get_observation_prompts()

        response = self.llm.generate_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # response_format={"type": "json_object"},
        )
        
        def response_parse(response_text):
            print(response_text)
            results = []
            for line in response_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                matches = [match.group(1) for match in self.PATTERN_V1.finditer(line)]
                if matches:
                    results.append(matches[2])
            return results

        try:
            new_retrieved_obs = response_parse(response)
        except Exception as e:
            logging.error(f"Error in new_retrieved_obs: {e}")
            new_retrieved_obs = []

        return new_retrieved_obs      