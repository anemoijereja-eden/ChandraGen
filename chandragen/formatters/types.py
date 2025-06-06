from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FormatterFlags:
    """Object used to store data used to communicate the current state of the formatting process to formatter modules"""

    in_preformat: bool = False
    in_multiline: bool = False
    active_multiline_formatter: str | None = None
    buffer_until_empty_line: list[str] = field(default_factory=list[str])


# priority levels:
# 0: Critical           -   Preprocess metadata, fix anything outright broken
# 1: Structural cleanup -   Fix anything that looks weird but is overall fine
# 2: Content Formatters -   Convert in-line formatting
# 3: Cosmetic           -   Fix minor style issues
# 4: Postprocessors     -   small, minor tweaks to the final document
# 5: Optional           -   clean up minor formatting issues like extra spaces or newlines
# 255: No Priority      -   Default assigned to formatters where order does not matter and you don't care enough to set it.


class LineFormatter(ABC):
    """
    Base class describing a line-formatting module

    Properties:
        Name: The name used to refer to the formatter module internally and externally.
        Description: multi-line string that will be presented to the end user when they query the formatter metadata.
        valid_types: list of mimetypes supported by the formatter module. currently unimplemented.
        priority: defines the order formatters will be run in. see documentation for what values mean.

    Methods:
        create: class method that generates the formatter instance
        apply: runs the formatter logic. called when the formatter is invoked, must take the line, config, and flags then return the formatted line.
    """

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
    """
    Base class describing a multiline-formatting module

    Properties:
        Name: The name used to refer to the formatter module internally and externally.
        Description: multi-line string that will be presented to the end user when they query the formatter metadata.
        valid_types: list of mimetypes supported by the formatter module. currently unimplemented.
        start_pattern: regex used to match the beginning of a multiline object
        end_pattern: regex used to match the end of a multiline object
        priority: defines the order formatters will be run in. see documentation for what values mean.

    Methods:
        create: class method that generates the formatter instance
        apply: runs the formatter logic. called when the formatter is invoked, must take the set of lines, config, and flags then return the formatted set of lines.
    """

    def __init__(
        self,
        name: str,
        description: str,
        valid_types: list[str],
        start_pattern: str,
        end_pattern: str,
        priority: int = 255,
    ):
        self.name: str = name
        self.description: str = description
        self.valid_types: list[str] = valid_types
        self.start_pattern: str = start_pattern  # regex to start buffering
        self.end_pattern: str = end_pattern  # regex to end buffering
        self.priority: int = priority

    @classmethod
    @abstractmethod
    def create(cls) -> MultilineFormatter:
        pass

    @abstractmethod
    def apply(self, buffer: list[str], config: FormatterConfig, flags: FormatterFlags) -> list[str]:
        pass


class DocumentPreprocessor(ABC):
    """
    Base class describing a document pre-processing module

    Properties:
        Name: The name used to refer to the formatter module internally and externally.
        Description: multi-line string that will be presented to the end user when they query the formatter metadata.
        valid_types: list of mimetypes supported by the formatter module. currently unimplemented.
        priority: defines the order formatters will be run in. see documentation for what values mean.

    Methods:
        create: class method that generates the formatter instance
        apply: runs the formatter logic. called when the formatter is invoked, must take the document and config, then return the formatted document.
    """

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
    def apply(self, document: list[str], config: FormatterConfig) -> list[str]:
        pass


@dataclass
class FormatterRegistry:
    """
    Object used to house the registry of formatter modules
    This method of storing the registry allows you to use dot notation to pull out the desired types of formatters, eg registry.line[name]

    attributes:
        line: the registry of line-formatters
        multiline: the registry of multiline formatters
        preprocessor: the registry of document pre-processors
    """

    line: dict[str, LineFormatter] = field(default_factory=dict[str, LineFormatter])
    multiline: dict[str, MultilineFormatter] = field(default_factory=dict[str, MultilineFormatter])
    preprocessor: dict[str, DocumentPreprocessor] = field(default_factory=dict[str, DocumentPreprocessor])


@dataclass
class FormatterConfig:
    """
    object used to house a formatter pipeline configuration

    attributes:
        jobname: the name of the formatter job being run
        formatter_flags: used to pre-load a set of runtime flags

        heading: a pre-formatted gemini heading. used by the heading pre-processor
        heading_end_pattern: string representing an exact line to match for the end of the heading to replace.
        heading_strip_offset: how many lines to offset the heading cut by

        footing section is largely the same

        input_path: file to pull the source document from
        output_path: file to push the results to

        preformatted_unicode_columns: number of text colums preformatted text blocks should take up

        enabled_formatters: list of module names to use during formatting

    """

    jobname: str = ""
    formatter_flags: dict[str, bool | int | str] = field(default_factory=dict[str, bool | int | str])

    heading: str | None = None
    heading_end_pattern: str | None = None
    heading_strip_offset: int = 0

    footing: str | None = None
    footing_start_pattern: str | None = None
    footing_strip_offset: int = 0

    input_path: Path | None = None
    output_path: Path | None = None

    preformatted_unicode_columns: int = 80

    enabled_formatters: list[str] = field(default_factory=list[str])
