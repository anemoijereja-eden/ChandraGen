import re

from loguru import logger

from chandragen.formatters.registry import FORMATTER_REGISTRY, import_builtin_formatters
from chandragen.formatters.types import (
    DocumentPreprocessor,
    FormatterConfig,
    LineFormatter,
    MultilineFormatter,
)
from chandragen.formatters.types import FormatterFlags
from chandragen.plugins import import_all_plugins

# Load modules immediately during import time.
import_all_plugins()
import_builtin_formatters()


class DocumentFormatter:
    """
    implements the formatting module that converts documents

    args:
        config: A FormatterConfig object describing the pipeline
        flags: A FormatterFlags object containing the initial flag data

    methods:
        format_document:
            takes a list of strings representing an input document, runs it through the pipeline, and returns the results.
    """

    def __init__(self, config: FormatterConfig, flags: FormatterFlags):
        logger.debug("starting formatter")
        self.config = config
        self.flags = flags
        self.multiline_buffer: list[str] = []
        self.output_doc: list[str] = []

    def _apply_line_formatters(self, line: str) -> str:
        """
        Processes a single line of a document using the specified formatting pipeline.

        Arguments:
            line: A string representing the line to be formatted.

        Returns:
            A string representing the formatted line.
        """
        for name in self.config.enabled_formatters:
            formatter = FORMATTER_REGISTRY.line.get(name)
            if formatter:
                line = formatter.apply(line, self.flags)
        return line

    def _apply_preprocessors(self, document: list[str]) -> list[str]:
        """
        Pre-processes a document using the specified pipeline configuration.

        Args:
            document: The document to be processed.

        Returns:
            The processed document.
        """
        for formatter in self.config.enabled_formatters:
            preprocessor = FORMATTER_REGISTRY.preprocessor.get(formatter)
            if preprocessor:
                document = preprocessor.apply(document, self.config)
        return document

    def format_document(self, input_doc: list[str]) -> list[str]:
        """Format Document

        Apply formatting to a list of strings, where each string represents a line in a document, and return the formatted result.

        Arguments:
            input_doc (list[str]): The document to be formatted.

        Returns:
            list[str]: The formatted document.
        """
        working_doc: list[str] = self._apply_preprocessors(input_doc)

        for line in working_doc:
            self._process_line(line)

        return self.output_doc

    def _process_line(self, line: str) -> None:
        """
        Runs a line through the formatting pipeline.
        Args:
            line (str): the line of the document to process
        """
        if line.startswith("```"):
            self.flags.in_preformat = not self.flags.in_preformat

        working_line = self._apply_line_formatters(line)

        if working_line.isspace() and self.flags.buffer_until_empty_line:
            self._flush_buffered_content()

        if not self.flags.in_multiline:
            self._check_and_start_multiline(working_line)

        if self.flags.in_multiline and self.flags.active_multiline_formatter:
            active_formatter = FORMATTER_REGISTRY.multiline.get(self.flags.active_multiline_formatter)
            if not active_formatter:
                return

            if re.match(active_formatter.end_pattern, line):
                self._end_multiline_formatting(active_formatter)
                return

            self.multiline_buffer.append(line)
        else:
            self.output_doc.append(line)

    def _flush_buffered_content(self) -> None:
        """
        Moves all buffered content into the output document and clears the buffer.

        This is typically called when an empty line is encountered, and the buffer is
        managed using the 'buffer_until_empty_line' flag.
        """
        self.output_doc += self.flags.buffer_until_empty_line
        self.flags.buffer_until_empty_line.clear()

    def _check_and_start_multiline(self, line: str) -> None:
        """
        Checks if a line initiates a multiline formatting block using enabled
        multiline formatters. If matched, sets the flags to indicate that
        multiline formatting is active.

        Args:
            line: The current line being processed.
        """
        for name in self.config.enabled_formatters:
            formatter = FORMATTER_REGISTRY.multiline.get(name)
            if formatter and re.match(formatter.start_pattern, line):
                self.flags.in_multiline = True
                self.flags.active_multiline_formatter = formatter.name
                break

    def _end_multiline_formatting(self, formatter: MultilineFormatter) -> None:
        """
        Ends the multiline formatting block and processes all buffered lines, then appends the results to the output document

        Args:
            formatter: the MultilineFormatter object to apply to buffered lines
        """
        self.flags.in_multiline = False
        self.flags.active_multiline_formatter = None
        formatted_buffer = formatter.apply(self.multiline_buffer, self.config, self.flags)
        self.output_doc += formatted_buffer
        self.multiline_buffer.clear()


# Function used to run the formatter module on a document.
def apply_formatting_to_file(config: FormatterConfig) -> bool:
    """
    Formats a document based on the provided configuration paths.

    This function reads a document from the input path specified in
    the configuration, applies formatting to its contents using
    FormatterConfig settings, and writes the formatted content to the
    output path. If the input or output path is not specified, it logs
    an error and returns False.

    Args:
        config (FormatterConfig): Configuration object containing input
                                  and output file paths and formatting
                                  settings.

    Returns:
        bool: True if the formatting and writing operations are successful,
              False if there was an error with the input/output paths.
    """
    if config.input_path is None or config.output_path is None:
        logger.error("Formatter error: input or output path not specified")
        return False

    # Grab the file, then split it into a 2D list for ease of manipulation
    with config.input_path.open() as f:
        input_file = f.readlines()

    # TODO: implement the formatter flag frontloading logic
    flags = FormatterFlags()
    # format the input doc and write the results to the output doc
    formatter = DocumentFormatter(config, flags)
    gemtext = f"{''.join(formatter.format_document(input_file))}"

    with config.output_path.open("w", encoding="utf-8") as page:
        page.write(gemtext)

    return True


__all__ = [
    "DocumentPreprocessor",
    "LineFormatter",
    "MultilineFormatter",
    "apply_formatting_to_file",
]
