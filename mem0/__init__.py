import importlib.metadata

__version__ = importlib.metadata.version("mem0ai")

from mem0.client.main import MemoryClient  # noqa
from mem0.memory.main import Memory  # noqa
from mem0_avater.mem0.memory_avater.main import AvaterMemory  # noqa
