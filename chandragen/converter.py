import re 
from chandragen.formatters import FORMATTER_REGISTRY
from chandragen.types import FormatterFlags as Flags, JobConfig as Config

# document pre-processors
# formatters that make changes to the document before running it through the pipeline

def strip_heading(document: list, config: Config) -> list:
    if config.heading is None or config.heading_end_pattern is None:
        print("Error! cannot strip heading without defined replacement and ending pattern")
        return document
    heading_end = document.index(config.heading_end_pattern) + config.heading_strip_offset
    del document[0:heading_end]
    heading = config.heading.splitlines(keepends=True)
    document = heading + document
    return document

def strip_footing(document: list, config: Config) -> list:
    if config.footing is None or config.footing_start_pattern is None:
        print("Error! cannot strip footing without defined replacement and starting pattern")
        return document
    footer_start = document.index(config.footing_start_pattern) + config.footing_strip_offset
    del document[footer_start:]
    footer = config.footing.splitlines(keepends=True)
    document.extend(footer)
    return document


# multiline formatters
        
# Line formatters
def config_enabled(config: dict, key: str) -> bool:
    return config.get(key, False)


def apply_line_formatters(line: str, config: Config, flags: Flags) -> str:
    for name in config.enabled_formatters:
        formatter = FORMATTER_REGISTRY.line.get(name)
        if formatter:
            line = formatter.apply(line, flags)
    return line

def format_document(input_doc: list, config: Config) -> list:
    #Global registers for the iteration logic to use
    multiline_buffer:   list  = []     # 2D list that's used to buffer multiline formatting
    output_doc:         list  = []     # The buffer for the final document
    flags = Flags()
    # Main Iterator
    # this is the beating heart of this conversion tool. it runs through each line and:
    # - runs the line through a line-formatting pipeline
    # - Pushes multi-line formatting types into a buffer to run through multi-line formatters
    for index, line in enumerate(input_doc):
        if line.startswith("```"):
            flags.in_preformat = not flags.in_preformat
        line = apply_line_formatters(line, config, flags)
        for name in config.enabled_formatters:
            formatter = FORMATTER_REGISTRY.multiline.get(name)
            if not formatter:
                continue
            if not re.match(formatter.start_pattern, line):
                continue
            flags.in_multiline = True
            flags.active_multiline_formatter = formatter.name
        if flags.in_multiline and flags.active_multiline_formatter is not None:
            active_multiline_formatter = FORMATTER_REGISTRY.multiline.get(flags.active_multiline_formatter)
            if active_multiline_formatter is None:
                continue
            if re.match(active_multiline_formatter.end_pattern, line):
                # We're done building the multi-line buffer, format it and push it to the final doc!
                flags.in_multiline = False
                flags.active_multiline_formatter = None
                multiline_buffer = active_multiline_formatter.apply(multiline_buffer, config, flags)
                output_doc += multiline_buffer # append the formatted buffer to the document
                multiline_buffer.clear()
                continue
            multiline_buffer.append(line)
        else:
            output_doc.append(line)
    return output_doc
 
def apply_formatting_to_file(config: Config) -> bool:
    if config.input_path is None or config.output_path is None:
        print("Error! input or output path not specified")
        return False

    # Grab the file, then split it into a 2D list for ease of manipulation
    with open(config.input_path) as f:
        input_file = f.readlines()

    # Run document pre-processors before pushing it into the formatting pipeline
    for formatter in config.enabled_formatters:
        preprocessor = FORMATTER_REGISTRY.preprocessor.get(formatter)
        if preprocessor:
            input_file = preprocessor.apply(input_file, config) 

    # format the input doc and write the results to the output doc
    gemtext = f"{''.join(format_document(input_file, config))}"

    with open(config.output_path, "w", encoding="utf-8") as page:
        page.write(gemtext)

    return True
