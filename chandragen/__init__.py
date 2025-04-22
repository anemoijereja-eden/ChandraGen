import chandragen.plugins as plugins
from chandragen.__main__ import run_config

# Load all dynamic plugins as soon as chandragen starts
plugins.import_all_plugins()

__version__ = "0.0.0"

__all__ = [
    "run_config"
]