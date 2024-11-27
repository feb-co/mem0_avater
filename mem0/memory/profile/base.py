import copy
import json
import logging
import asyncio
from typing import Union

from mem0.configs.base import MemoryConfig
from mem0.configs.prompts import profile_prompts

from mem0.database.profile.my_sql import Mysql
from mem0.llms.azure_openai_structured import AzureOpenAIStructuredLLM
from mem0.utils.factory import ProfileDBFactory, LlmFactory


class MemoryProfile:
    def __init__(self, config: MemoryConfig = MemoryConfig()):
        self.config = config

        self.profile_schema_cls = self.config.profile_schema
        self.llm: Union[AzureOpenAIStructuredLLM] = LlmFactory.create(self.config.llm.provider, self.config.llm.config)
        self.db: Union[Mysql] = ProfileDBFactory.create(
            self.config.profile_db.provider,
            self.config.profile_db.config
        )

    def _get_profile_info(self, profile):
        profiles_info = []
        for keyword in profile.get_profile_keys():
            profiles_info.append(f"**{keyword}**: {profile.get_profile_description(keyword)}")
        return profiles_info

    async def get_profile(self, profile_id: int):
        """
        Get user profile by user ID.

        Args:
            user_id (int): ID of the user to get profile for.

        Returns:
            profile_schema_cls: User profile data.
        """
        profile = await self.db.get_profile(profile_id)
        return self.profile_schema_cls.from_json_str(profile)

    async def _set_profile(self, profile_id: int, profile):
        old_profile = await self.db.get_profile(profile_id)
        if old_profile is None:
            await self.db.insert_profile(profile_id, profile)
        else:
            await self.db.update_profile(profile_id, profile)

    async def _get_conflict_label(self, profile, messages: list):
        prompt = profile_prompts.CLASSIFY_CONFLICT_PROMPT.format(
            information_types=profile.get_profile_keys(),
            few_shots=profile_prompts.CLASSIFY_CONFLICT_FEW_SHOTS,
            history_profile=profile,
            conversation=messages,
        )
        try:
            response = self.llm.generate_response(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ]
            )
        except Exception as e:
            logging.error(f"[Profile Module] Error in get_conflict_label: {e}")
            response = None

        if response is None:
            return False

        if response.lower() == "a":
            return True
        else:
            return False

    async def _get_nonconflict_label(self, profile, messages: list):
        prompt = profile_prompts.CLASSIFY_NON_CONFLICT_PROMPT.format(
            few_shots=profile_prompts.CLASSIFY_NON_CONFLICT_FEW_SHOTS,
            conversation=messages,
            information_types=profile.get_profile_keys(),
        )

        try:
            response = self.llm.generate_response(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ]
            )
        except Exception as e:
            logging.error(f"[Profile Module] Error in get_nonconflict_label: {e}")
            response = None

        if response is None:
            return False

        if response.lower() in ("a", "c"):
            return True
        else:
            return False

    async def _update_profile(self, profile_id, messages, profile):
        filter_profile = {}
        for category in self.profile_schema_cls.get_profile_category():
            sub_dict = getattr(profile, category)
            for sub_key, field in sub_dict.items():
                if field.value not in {None, "None"}:
                    filter_profile[sub_key] = {"value": field.value}

        prompt = profile_prompts.EXTRACT_PROFILE_PROMPT.format(
            profile_info="\n".join(self.get_profile_info()),
            conversation=messages,
            few_shots=profile_prompts.EXTRACT_PROFILE_FEW_SHOTS,
            history_profile=filter_profile,
        )

        try:
            response = self.llm.generate_response(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            profile_dict = json.loads(response)
        except Exception as e:
            logging.error(f"[Profile Module] Error in update_profile: {e}")
            profile_dict = None
        
        if profile_dict is not None:
            for key in profile_dict:
                profile.set_value(key, profile_dict[key])

        await self._set_profile(profile_id, profile)

    async def add(
        self,
        messages,
        user_id=None,
        agent_id=None,
        run_id=None,
    ) -> None:
        """
        Add or update profile information based on conversation messages.

        This method analyzes conversation messages to extract and update profile information.
        It handles potential conflicts in profile data and ensures proper profile updates.

        Args:
            messages (Union[str, List[Dict[str, str]]]): The conversation messages to analyze.
                Can be a string or a list of message dictionaries with 'role' and 'content'.
            user_id (Optional[int]): The ID of the user whose profile to update
            agent_id (Optional[int]): The ID of the agent whose profile to update
            run_id (Optional[int]): The ID of the run whose profile to update

        Raises:
            ValueError: If no ID is provided or if multiple IDs are provided simultaneously

        Note:
            - Only one of user_id, agent_id, or run_id should be provided
            - Messages are analyzed for both conflicts and non-conflicts with existing profile data
            - Profile updates are handled asynchronously if conflicts or non-conflicts are detected
        """
        # Count number of non-empty IDs
        non_empty_ids = sum(1 for id in (user_id, agent_id, run_id) if id is not None)

        # Check if exactly one ID is provided
        if non_empty_ids == 0:
            raise ValueError("One of user_id, agent_id or run_id must be provided")
        elif non_empty_ids > 1:
            raise ValueError("Only one of user_id, agent_id or run_id can be provided")

        profile_id = None
        # Set the corresponding ID in filters and metadata
        if user_id is not None:
            profile_id = user_id
        elif agent_id is not None:
            profile_id = agent_id
        elif run_id is not None:
            profile_id = run_id

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        profile = self.get_profile(profile_id)

        # conflict_label, old_profile = await self._get_conflict_label(profile_id, messages)
        conflict_label, nonconflict_label = await asyncio.gather(
            self._get_conflict_label(profile, messages),
            self._get_nonconflict_label(profile, messages)
        )

        if conflict_label or nonconflict_label:
            asyncio.create_task(
                self._update_profile(profile_id, messages)
            )
