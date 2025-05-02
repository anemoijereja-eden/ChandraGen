from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Types used to pass data around the formatter system

# FormatterFlags are passed between formatters in the formatter pipeline, and are intended to facilitate some basic IPC functinality as well as allow simple configs.
# FormatterFlags are intended to be possible to overwrite with chandragen.types.JobConfig.formatter_flags at pipeline invokation
@dataclass
class FormatterFlags:
    in_preformat: bool = False
    in_multiline: bool = False
    active_multiline_formatter: str | None = None
    buffer_until_empty_line: list[str] = field(default_factory=list[str])

   
@dataclass
class ConverterConfig:
    jobname: str                         = ""
    formatter_flags: dict[str, bool]     = field(default_factory=dict[str, bool])
    heading: str | None                  = None
    heading_end_pattern: str | None      = None
    heading_strip_offset: int            = 0

    footing: str | None                  = None
    footing_start_pattern: str | None    = None
    footing_strip_offset: int            = 0

    input_path: Path | None              = None
    output_path: Path | None             = None

    preformatted_unicode_columns: int    = 80

    enabled_formatters: list[str]        = field(default_factory=list[str])   

# Base Formatter Classes
# name: specifies how the formatter will be called and entered to the registry
# description: used for internal documentation tools, has no bearing on functionality.
# valid_types: list of file extensions the formatter is good for. currently unimplemented.
# priority: Stores a number from 0 to 5 specifying where the formatter belongs in the pipeline. this will be used to sort the registry and determine the order they run in.
# levels:
# 0: Critical           -   Preprocess metadata, fix anything outright broken
# 1: Structural cleanup -   Fix anything that looks weird but is overall fine
# 2: Content Formatters -   Convert in-line formatting
# 3: Cosmetic           -   Fix minor style issues
# 4: Postprocessors     -   small, minor tweaks to the final document
# 5: Optional           -   clean up minor formatting issues like extra spaces or newlines
# 255: No Priority      -   Default assigned to formatters where order does not matter and you don't care enough to set it.

class LineFormatter(ABC):
    def __init__(self, name: str, description: str, valid_types: list[str], priority: int = 255):
        self.name: str = name
        self.description: str = description
        self.valid_types: list[str] = valid_types
        self.priority: int = priority

    @classmethod
    @abstractmethod
    def create(cls) -> LineFormatter:
        pass

    @abstractmethod
    def apply(self, line: str, flags: FormatterFlags) -> str:
        pass

class MultilineFormatter(ABC):
    def __init__(self, name: str, description: str, valid_types: list[str], start_pattern: str, end_pattern: str, priority: int = 255):
        self.name: str = name
        self.description: str = description
        self.valid_types: list[str] = valid_types
        self.start_pattern: str = start_pattern # regex to start buffering
        self.end_pattern: str = end_pattern    # regex to end buffering
        self.priority: int = priority

    @classmethod
    @abstractmethod
    def create(cls) -> MultilineFormatter:
        pass

    @abstractmethod
    def apply(self, buffer: list[str], config: ConverterConfig, flags: FormatterFlags) -> list[str]:
        pass

class DocumentPreprocessor(ABC):
    def __init__(self, name: str, description: str, valid_types: list[str], priority: int = 255):
        self.name: str = name
        self.description: str = description
        self.valid_types: list[str] = valid_types
        self.priority: int = priority

    @classmethod
    @abstractmethod
    def create(cls) -> DocumentPreprocessor:
        pass
    
    @abstractmethod
    def apply(self, document: list[str], config: ConverterConfig) -> list[str]:
        pass

# Dataclass for the formatter registry that splits it cleanly into sections for each formater type
@dataclass
class FormatterRegistry:
    line: dict[str, LineFormatter] = field(default_factory=dict[str, LineFormatter])
    multiline: dict[str, MultilineFormatter] = field(default_factory=dict[str, MultilineFormatter])
    preprocessor: dict[str, DocumentPreprocessor] = field(default_factory=dict[str, DocumentPreprocessor])
    
# Dataclass for holding context about the currently running chandragen instance.
@dataclass
class SystemConfig:
    invoked_command: str
    config_path: Path
    start_time: datetime
    debug_jobs: bool = False
    
