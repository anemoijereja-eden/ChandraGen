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
class LineFormatter(ABC):
    def __init__(self, name: str, description: str, valid_types: list[str]):
        self.name: str = name
        self.description: str = description
        self.valid_types: list[str] = valid_types

    @classmethod
    @abstractmethod
    def create(cls) -> LineFormatter:
        pass

    @abstractmethod
    def apply(self, line: str, flags: FormatterFlags) -> str:
        pass

class MultilineFormatter(ABC):
    def __init__(self, name: str, description: str, valid_types: list[str], start_pattern: str, end_pattern: str):
        self.name: str = name
        self.description: str = description
        self.valid_types: list[str] = valid_types
        self.start_pattern: str = start_pattern # regex to start buffering
        self.end_pattern: str = end_pattern    # regex to end buffering

    @classmethod
    @abstractmethod
    def create(cls) -> MultilineFormatter:
        pass

    @abstractmethod
    def apply(self, buffer: list[str], config: ConverterConfig, flags: FormatterFlags) -> list[str]:
        pass

class DocumentPreprocessor(ABC):
    def __init__(self, name: str, description: str, valid_types: list[str]):
        self.name: str = name
        self.description: str = description
        self.valid_types: list[str] = valid_types

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
    
