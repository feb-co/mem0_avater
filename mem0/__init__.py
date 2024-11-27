import importlib.metadata

__version__ = importlib.metadata.version("mem0_avater")

from mem0.client.main import MemoryClient  # noqa
from mem0.memory.memory import Memory  # noqa
