import re
import textwrap
from pathlib import Path

# TODO: make config dict redefinable with command line args
# TODO: make an example/default confdict that isn't tied to atl
#This confdict is the one written for the all things linux code of conduct.
example_config: dict = { 
# If heading or footing is defined in a conf, you're also expected to include a start/end pattern that matches a line's content
"heading": r"""
```
  _____        __      ____  ___  _____             __         __
 / ___/__  ___/ /__   / __ \/ _/ / ___/__  ___  ___/ /_ ______/ /_
/ /__/ _ \/ _  / -_) / /_/ / _/ / /__/ _ \/ _ \/ _  / // / __/ __/
\___/\___/\_,_/\__/  \____/_/   \___/\___/_//_/\_,_/\_,_/\__/\__/
```
""",
"heading_end_pattern" : "<!-- END doctoc generated TOC please keep comment here to allow auto update -->\n",
"heading_strip_offset_lines" : 2,

"footing": r"""
## Contributors
=> https://contrib.rocks Made with contrib.rocks
=> https://contrib.rocks/image?repo=allthingslinux/code-of-conduct Contributors
""",
"footing_start_pattern" : "## Contributors\n",
"footing_strip_offset_lines":   0,
# input and output pats are required to run the file formatter.
"input_path":                   Path("./code-of-conduct/README.md"),
"output_path":                  Path("./allthingslinux.org/code-of-conduct.gmi"),
# standard column count for all formatters that output to preformatted text blocks with ascii art
"preformatted_unicode_columns": 80,
# pipeline config. these define which formatters will be run on the document.
"strip_inline_formatting":      True,
"convert_bullet_point_links":   True,
"format_unicode_tables":        True,
"convert_known_mdx_components": True,
"strip_imports_exports":        True,
"strip_jsx_tags":               True,
"normalize_codeblocks":         True,
}

# document pre-processors
# formatters that make changes to the document before running it through the pipeline

def strip_heading(document: list, config: dict) -> list:
    heading_end = document.index(config["heading_end_pattern"]) + config["heading_strip_offset_lines"]
    del document[0:heading_end]
    heading = config["heading"].splitlines(keepends=True)
    document = heading + document
    return document

def strip_footing(document: list, config: dict) -> list:
    footer_start = document.index(config["footing_start_pattern"]) + config["footing_strip_offset_lines"]
    del document[footer_start:]
    document.insert(len(document), config["footing"])
    return document

# multiline formatters
def format_table(multiline_buffer: list, config: dict) -> list:
    table = [i[2:-2].split(" | ") for i in multiline_buffer]   # take the buffer and convert the table lines into a 2d list
    table_width: int = config["preformatted_unicode_columns"]
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

def apply_line_formatters(line: str, config: dict) -> str:
    if config_enabled(config, "strip_inline_formatting"):
        line = strip_inline_markdown(line)
    if config_enabled(config, "convert_bullet_point_links"):
        line = convert_links(line)
    if config_enabled(config, "convert_known_mdx_components"):
        line = convert_known_components(line)
    if config_enabled(config, "strip_imports_exports"):
        line = strip_imports_exports(line)
    if config_enabled(config, "strip_jsx_tags"):
        line = strip_jsx_tags(line)
    if config_enabled(config, "normalize_codeblocks"):
        line = normalize_code_blocks(line)
    return line

def convert_links(line: str) -> str:
    #Convert "- [label](url)" markdown link lines to "=> url label" gemtext links
    if line.startswith("- ["):
        # strip the first 3 characters "- [" off the line, then break it in half at the ](
        link = line[3:].split("](")
        # Since we have to flip the fields around, we also need to strip the newline and add one at the end.
        return f"=> {link[1].replace(")\n","")} {link[0]}\n"
    return line

def strip_inline_markdown(line: str) -> str:
    #set up a regex method to remove inline markdown
    inline_md_replacements = {"*":"","**":"","***":"","_":"","__":"","___":"",}
    inline_md_pattern = re.compile("|".join(re.escape(old) for old in inline_md_replacements))
    # regex it all out
    return f"{line[0:2]}{inline_md_pattern.sub(lambda match: inline_md_replacements[match.group(0)], line[2:])}"

# MDX formatters
def strip_imports_exports(line: str) -> str:
    if line.strip().startswith(("import ", "export ")):
        return ""
    return line

def strip_jsx_tags(line: str) -> str:
    if line.strip().startswith("<") and not line.strip().startswith(("<!--", "<!DOCTYPE")):
        return ""  # or convert it if you want special behavior!
    return line

def strip_jsx_expressions(line: str) -> str:
    return re.sub(r"{.*?}", "", line)

def convert_known_components(line: str) -> str:
    component_map = {
        "<Note>": "NOTE:",
        "</Note>": "",
        "<Warning>": "WARNING:",
        "</Warning>": ""
    }
    for jsx, gem in component_map.items():
        line = line.replace(jsx, gem)
    return line

def normalize_code_blocks(line: str) -> str:
    return line if not line.startswith("```") else "```\n"

def format_document(input_doc: list, config: dict) -> list:
    #Global registers for the iteration logic to use
    format_multiline: bool  = False  # switches iteration logic between single and multiple line formatter modes
    multiline_buffer: list  = []     # 2D list that's used to buffer multiline formatting
    output_doc:       list  = []     # The buffer for the final document

    # Main Iterator
    # this is the beating heart of this conversion tool. it runs through each line and:
    # - runs the line through a line-formatting pipeline
    # - Pushes multi-line formatting types into a buffer to run through multi-line formatters
    for index, line in enumerate(input_doc):
        line = apply_line_formatters(line, config)
        if format_multiline:
            if line.startswith("|"): 
                multiline_buffer.append(line)
            else:
                # We're done building the multi-line buffer, format it and push it to the final doc!
                format_multiline = False
                multiline_buffer = format_table(multiline_buffer, config) if config["format_unicode_tables"] else multiline_buffer
                output_doc += multiline_buffer # append the formatted buffer to the document
                multiline_buffer.clear()
        else:
            if line.startswith("|"):
                format_multiline = True
                multiline_buffer.append(line)
            else:
                output_doc.append(line)
    return output_doc
 
def apply_formatting_to_file(config: dict) -> bool:
    if config["input_path"] is None or config["output_path"] is None:
        print("Error! input or output path not specified")
        return False
    
    # Grab the file, then split it into a 2D list for ease of manipulation
    with open(config["input_path"]) as f:
        input_file = f.readlines()
               
    # Run document pre-processors before pushing it into the formatting pipeline
    if config["heading"] is not None:
        input_file = strip_heading(input_file, config)
    
    if config["footing"] is not None:
        input_file = strip_footing(input_file, config)
               
    # format the input doc and write the results to the output doc
    gemtext = f"{''.join(format_document(input_file, config))}"
    print(repr(gemtext))
    with open(config["output_path"], "w", encoding="utf-8") as page:
        page.write(gemtext)    
    return True
