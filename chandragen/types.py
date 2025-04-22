from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FormatterFlags:
    in_preformat: bool = False
    in_multiline: bool = False

@dataclass
class JobConfig:
    jobname: str                         = ""
    formatter_flags: dict[str, bool]     = field(default_factory=dict)
    heading: Optional[str]               = None
    heading_end_pattern: Optional[str]   = None
    heading_strip_offset: int            = 0

    footing: Optional[str]               = None
    footing_start_pattern: Optional[str] = None
    footing_strip_offset: int            = 0

    input_path: Optional[Path]           = None
    output_path: Optional[Path]          = None

    preformatted_unicode_columns: int    = 80

    enabled_formatters: list[str]        = field(default_factory=list)   

