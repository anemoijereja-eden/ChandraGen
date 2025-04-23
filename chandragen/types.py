from typing import Optional
from typing import Dict
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod

# Types used to pass data around the formatter system

# FormatterFlags are passed between formatters in the formatter pipeline, and are intended to facilitate some basic IPC functinality as well as allow simple configs.
# FormatterFlags are intended to be possible to overwrite with chandragen.types.JobConfig.formatter_flags at pipeline invokation
@dataclass
class FormatterFlags:
    in_preformat: bool = False
    in_multiline: bool = False
    active_multiline_formatter: str | None = None

# a JobConfig contains the information needed by the converter to properly convert a file.
# JobConfigs are generated in chandragen.__main__ and passed to chandragen.converter when chandragen.converter.apply_formatting_to_file is invoked 
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

# Base Formatter Classes 
class LineFormatter(ABC):
    name: str
    description: str
    valid_types: list[str]
    
    @abstractmethod
    def apply(self, line: str, flags: FormatterFlags) -> str:
        pass

class MultilineFormatter(ABC):
    name: str
    description: str
    valid_types: list[str]
    start_pattern: str  # regex to start buffering
    end_pattern: str    # regex to end buffering

    @abstractmethod
    def apply(self, buffer: list[str], config: JobConfig, flags: FormatterFlags) -> list[str]:
        pass

class DocumentPreprocessor(ABC):
    name: str
    description: str
    valid_types: list[str]

    @abstractmethod
    def apply(self, document: list[str], config: JobConfig) -> list[str]:
        pass

# Dataclass for the formatter registry that splits it cleanly into sections for each formater type
@dataclass
class FormatterRegistry:
    line: Dict[str, "LineFormatter"] = field(default_factory=dict)
    multiline: Dict[str, "MultilineFormatter"] = field(default_factory=dict)
    preprocessor: Dict[str, "DocumentPreprocessor"] = field(default_factory=dict)
