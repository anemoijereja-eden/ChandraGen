from datetime import UTC, datetime
from pathlib import Path

from chandragen.types import SystemConfig

__version__ = "0.0.0"
system_config: SystemConfig = SystemConfig(
    "None",
    Path("/"),
    datetime.now(UTC)
)

