import importlib
import pkgutil
import re

from chandragen.plugins import import_all_plugins
from chandragen.types import ConverterConfig as Config
from chandragen.types import DocumentPreprocessor, FormatterRegistry, LineFormatter, MultilineFormatter
from chandragen.types import FormatterFlags as Flags


def import_builtin_formatters():
    for _finder, modname, _ispkg in pkgutil.iter_modules(__path__):
        full_name = f"{__name__}.{modname}"
        importlib.import_module(full_name)

# To avoid import order shenanigans, ensure every module is loaded immediately when the formatter system is initialized
import_all_plugins()
import_builtin_formatters()

def build_formatter_registry() -> FormatterRegistry:
    
    line: dict[str, LineFormatter] = {}
    multiline: dict[str, MultilineFormatter] = {}
    preprocessors: dict[str, DocumentPreprocessor] = {}

    for subclass in LineFormatter.__subclasses__():
        formatter = subclass.create()
        line[formatter.name] = formatter

    for subclass in MultilineFormatter.__subclasses__():
        formatter = subclass.create()
        multiline[formatter.name] = formatter

    for subclass in DocumentPreprocessor.__subclasses__():
        formatter = subclass.create()
        preprocessors[formatter.name] = formatter

    return FormatterRegistry(
        line = line,
        multiline = multiline,
        preprocessor = preprocessors,
    )

FORMATTER_REGISTRY: FormatterRegistry = build_formatter_registry()


def apply_line_formatters(line: str, config: Config, flags: Flags) -> str:
    for name in config.enabled_formatters:
        formatter = FORMATTER_REGISTRY.line.get(name)
        if formatter:
            line = formatter.apply(line, flags)
    return line

def apply_preprocessors(document: list[str], config: Config) -> list[str]:
    for formatter in config.enabled_formatters:
        preprocessor = FORMATTER_REGISTRY.preprocessor.get(formatter)
        if preprocessor:
            document = preprocessor.apply(document, config)
    return document


def format_document(input_doc: list[str], config: Config) -> list[str]:
    # Prepare the document by applying preprocessors to it
    working_doc = apply_preprocessors(input_doc, config)
    
    #Global registers for the iteration logic to use
    multiline_buffer: list[str]  = []     # 2D list that's used to buffer multiline formatting
    output_doc:         list[str]  = []     # The buffer for the final document
    flags = Flags()
    # Main Iterator
    # this is the beating heart of this conversion tool. it runs through each line and:
    # - runs the line through a line-formatting pipeline
    # - Pushes multi-line formatting into a buffer to run through multi-line formatters
    for line in working_doc:
        working_line = line
        if line.startswith("```"):
            flags.in_preformat = not flags.in_preformat
        working_line = apply_line_formatters(working_line, config, flags)
        
        if working_line.isspace() and len(flags.buffer_until_empty_line) > 0:
            # This is an empty line, if we have something buffered until after a paragraph, dump it in!
            output_doc += flags.buffer_until_empty_line
            flags.buffer_until_empty_line.clear()
            
        # Checks if a line can start a multiline formatter
        for name in config.enabled_formatters:
            formatter = FORMATTER_REGISTRY.multiline.get(name)
            if not formatter:
                continue
            if not re.match(formatter.start_pattern, working_line):
                continue
            flags.in_multiline = True
            flags.active_multiline_formatter = formatter.name
        
        # Applies multiline formatters
        if flags.in_multiline and flags.active_multiline_formatter is not None:
            active_multiline_formatter = FORMATTER_REGISTRY.multiline.get(flags.active_multiline_formatter)
            if active_multiline_formatter is None:
                continue
            if re.match(active_multiline_formatter.end_pattern, working_line):
                # We're done building the multi-line buffer, format it and push it to the final doc!
                flags.in_multiline = False
                flags.active_multiline_formatter = None
                multiline_buffer = active_multiline_formatter.apply(multiline_buffer, config, flags)
                output_doc += multiline_buffer # append the formatted buffer to the document
                multiline_buffer.clear()
                continue
            multiline_buffer.append(working_line)
        else:
            output_doc.append(working_line)
    return output_doc
 
def apply_formatting_to_file(config: Config) -> bool:
    if config.input_path is None or config.output_path is None:
        print("Error! input or output path not specified")
        return False

    # Grab the file, then split it into a 2D list for ease of manipulation
    with config.input_path.open() as f:
        input_file = f.readlines()

    # format the input doc and write the results to the output doc
    gemtext = f"{''.join(format_document(input_file, config))}"

    with config.output_path.open("w", encoding="utf-8") as page:
        page.write(gemtext)

    return True