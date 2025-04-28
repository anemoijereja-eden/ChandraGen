from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConverterJob:
    jobname: str
    interval: str
    is_dir: bool
    is_recursive: bool
    input_path: Path
    output_path: Path
    formatter_flags: dict[str, bool]     = field(default_factory=dict[str, bool])
    heading: str | None                  = None
    heading_end_pattern: str | None      = None
    heading_strip_offset: int            = 0

    footing: str | None                  = None
    footing_start_pattern: str | None    = None
    footing_strip_offset: int            = 0

    preformatted_unicode_columns: int    = 80

    enabled_formatters: list[str]        = field(default_factory=list[str])   

