from typing import Union

from mem0.configs.base import MemoryConfig

from mem0.memory.base.base import MemoryBase
from mem0.memory.profile.base import MemoryProfile


class Memory(MemoryBase, MemoryProfile):
    """
    A class that combines memory storage and profile management functionality.
    Inherits from both MemoryBase for storing memories and MemoryProfile for managing user profiles.
    """
    def __init__(self, config: MemoryConfig = MemoryConfig()) -> None:
        """
        Initialize the Memory class with configuration.
        
        Args:
            config (MemoryConfig): Configuration object for memory and profile settings
        """
        MemoryBase.__init__(self, config)
        MemoryProfile.__init__(self, config)

    async def get_profile(self, profile_id):
        """
        Asynchronously retrieve a user's profile by their ID.
        
        Args:
            profile_id: The ID of the profile to retrieve
            
        Returns:
            The user profile data
        """
        return await self.get_profile(profile_id)

    async def update_profile(self, profile_id, message: Union[str|list]):
        """
        Asynchronously update a user's profile based on new message content.
        Uses MemoryProfile's add method directly to avoid name conflict with MemoryBase.add.
        
        Args:
            profile_id: The ID of the profile to update
            message (Union[str|list]): The message content used to update the profile
        """
        # Need to use MemoryProfile.add directly since self.add() would call MemoryBase.add
        # Using await since MemoryProfile.add is an async method
        await MemoryProfile.add(self, message, user_id=profile_id)
