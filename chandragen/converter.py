import textwrap
from chandragen.line_formatters import FORMATTER_REGISTRY
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
def format_table(multiline_buffer: list, config: Config) -> list:
    table = [i[2:-2].split(" | ") for i in multiline_buffer]   # take the buffer and convert the table lines into a 2d list
    table_width: int = config.preformatted_unicode_columns
    clean_table = []
    column_width = max(len(column.strip()) for column in table[0])
    for x, y in enumerate(table):               # strips the seperating line 
        if not all( char == '-' for char in y[0]):      # Check if first column of row is all dashes. if it is, it's a seperator row and should be discarded.
            clean0 = y[0].strip() # Generate cleaned version of columns 0 and 1
            clean1 = y[1].strip()
            wrapped_text = textwrap.wrap(clean1, width = (table_width - column_width) - 5)
            clean_table.append([clean0, wrapped_text[0]])
            for segment in wrapped_text[1:]:
                clean_table.append([" "*column_width, segment])
            clean_table.append(["",""]) # add a blank line between each row for readability
    
    final_table = [
        "```\n",
        f"┌{'─'*(column_width+2)}┬{'─'*((table_width - 3) - column_width)}┐\n",
        *[
            f"├{'─'*(column_width+2)}┼{'─'*((table_width - 3) - column_width)}┤\n" if idx == 1 else "" +
            f"│ {row[0] + ' '*(column_width - len(row[0]))} │ {row[1] + ' '*((table_width - 4) - (len(row[1]) + column_width))}│\n"
            for idx, row in enumerate(clean_table)
        ],
        f"└{'─'*(column_width+2)}┴{'─'*((table_width - 3) - column_width)}┘\n```\n"
    ]
    return final_table
        
# Line formatters
def config_enabled(config: dict, key: str) -> bool:
    return config.get(key, False)


def apply_line_formatters(line: str, config: Config, flags: Flags) -> str:
    for name in config.enabled_formatters:
        formatter = FORMATTER_REGISTRY.get(name)
        if formatter:
            line = formatter.apply(line, flags)
        else:
            print(f"⚠️  Formatter '{name}' not found in registry. Skipping.")
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
        if flags.in_multiline:
            if line.startswith("|"): 
                multiline_buffer.append(line)
            else:
                # We're done building the multi-line buffer, format it and push it to the final doc!
                flags.in_multiline = False
                multiline_buffer = format_table(multiline_buffer, config) if "format_unicode_tables" in config.enabled_formatters else multiline_buffer
                output_doc += multiline_buffer # append the formatted buffer to the document
                multiline_buffer.clear()
        else:
            if line.startswith("|"):
                flags.in_multiline = True
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
    if config.heading:
        input_file = strip_heading(input_file, config)

    if config.footing:
        input_file = strip_footing(input_file, config)

    # format the input doc and write the results to the output doc
    gemtext = f"{''.join(format_document(input_file, config))}"

    with open(config.output_path, "w", encoding="utf-8") as page:
        page.write(gemtext)

    return True
