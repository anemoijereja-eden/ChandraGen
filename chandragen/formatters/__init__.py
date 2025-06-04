import re

from loguru import logger

from chandragen.formatters.registry import FORMATTER_REGISTRY, import_builtin_formatters
from chandragen.formatters.types import (
    DocumentPreprocessor,
    FormatterConfig,
    LineFormatter,
    MultilineFormatter,
)
from chandragen.formatters.types import FormatterFlags as Flags
from chandragen.plugins import import_all_plugins

# To avoid import order shenanigans, ensure every module is loaded immediately when the formatter system is initialized
import_all_plugins()
import_builtin_formatters()


def apply_line_formatters(line: str, config: FormatterConfig, flags: Flags) -> str:
    for name in config.enabled_formatters:
        formatter = FORMATTER_REGISTRY.line.get(name)
        if formatter:
            line = formatter.apply(line, flags)
    return line


def apply_preprocessors(document: list[str], config: FormatterConfig) -> list[str]:
    for formatter in config.enabled_formatters:
        preprocessor = FORMATTER_REGISTRY.preprocessor.get(formatter)
        if preprocessor:
            document = preprocessor.apply(document, config)
    return document


def format_document(input_doc: list[str], config: FormatterConfig) -> list[str]:
    working_doc = apply_preprocessors(input_doc, config)

    # Global registers for the iteration logic to use
    multiline_buffer: list[str] = []  # 2D list that's used to buffer multiline formatting
    output_doc: list[str] = []  # The buffer for the final document
    flags = Flags()

    # Main Iterator
    # - Processes each line through a line-formatting pipeline
    # - Accumulates lines for multi-line formatting in a buffer

    for line in working_doc:
        working_line = line
        if line.startswith("```"):
            # Toggle preformatted code block flag
            flags.in_preformat = not flags.in_preformat
        working_line = apply_line_formatters(working_line, config, flags)

        if working_line.isspace() and flags.buffer_until_empty_line:
            # Empty line detected; flush buffered content, if any
            output_doc += flags.buffer_until_empty_line
            flags.buffer_until_empty_line.clear()

        # Check for possible start of a multi-line formatter
        for name in config.enabled_formatters:
            formatter = FORMATTER_REGISTRY.multiline.get(name)
            if not formatter:
                continue
            if not re.match(formatter.start_pattern, working_line):
                continue
            flags.in_multiline = True
            flags.active_multiline_formatter = formatter.name

        # Handle active multi-line formatters
        if flags.in_multiline and flags.active_multiline_formatter:
            active_formatter = FORMATTER_REGISTRY.multiline.get(flags.active_multiline_formatter)
            if not active_formatter:
                continue
            if re.match(active_formatter.end_pattern, working_line):
                # Multi-line buffer complete; format and output it
                flags.in_multiline = False
                flags.active_multiline_formatter = None
                formatted_buffer = active_formatter.apply(multiline_buffer, config, flags)
                output_doc += formatted_buffer
                multiline_buffer.clear()
                continue
            multiline_buffer.append(working_line)
        else:
            output_doc.append(working_line)
    return output_doc


def apply_formatting_to_file(config: FormatterConfig) -> bool:
    if config.input_path is None or config.output_path is None:
        logger.error("Formatter error: input or output path not specified")
        return False

    # Grab the file, then split it into a 2D list for ease of manipulation
    with config.input_path.open() as f:
        input_file = f.readlines()

    # format the input doc and write the results to the output doc
    gemtext = f"{''.join(format_document(input_file, config))}"

    with config.output_path.open("w", encoding="utf-8") as page:
        page.write(gemtext)

    return True


__all__ = [
    "DocumentPreprocessor",
    "LineFormatter",
    "MultilineFormatter",
    "apply_formatting_to_file",
]
