from mem0.configs.base import MemoryConfig, MemoryItem

from mem0.memory.base.base import MemoryBase
from mem0.memory.profile.base import MemoryProfile


class Memory(MemoryBase, MemoryProfile):
    def __init__(self, config: MemoryConfig = MemoryConfig()) -> None:
        MemoryBase.__init__(self, config)
        MemoryProfile.__init__(self, config)
