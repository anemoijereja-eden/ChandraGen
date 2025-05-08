from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# Dataclass for holding context about the currently running chandragen instance.
@dataclass
class SystemConfig:
    invoked_command: str
    config_path: Path
    start_time: datetime
    running: bool = True
    debug_jobs: bool = False
    scheduler_mode: str = "unspecified"
