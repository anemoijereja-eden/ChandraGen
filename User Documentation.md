# Welcome to ChandraGen!
ChandraGen is a modular ssg framework that outputs gemini pages.
ChandraGen's workflow is based around a modular conversion pipeline that builds documents from source markdown or mdx files.

## Formatters
A formatter is a unit of code in ChandraGen that modifies a document in some way. Formatters are loaded dynamically from the internal/built-in tools, as well as from external plug-ins.
ChandraGen formatters are pipelined, meaning that parts of a document are passed along between each formatter.
You can think of the formatting pipeline like an assembly line, with your document on a conveyor belt and workers assembling their own small piece as it goes down.
### Types of formatters
Chandragen formatters fall into one of three categories depending on how they work on a document:
- Document Pre-Processors
  - Take the entire source document and modify it before it reaches the main pipeline
  - Mostly used for formatters that cut out or rearrange large sections of a document
- Line Formatters
  - The simplest type of formatter, a line formatter takes a single line of a document, modifies it, and passes the modified document down.
  - line formatters have limited context on the rest of the document
  - these handle the majority of the conversion process
- Multi-line formatters
  - Multiline formatters handle formatting objects like tables that span several lines
  - these formatters use regex to find the beginning and end of a section that matches their criteria, and then modify these entire sections.
  - best for complex formatting that spans several lines, but doesn't need to be handled by manipulating the entire document.

### Pipeline order
Each formatter type occupies a set position in the assembly line.
individual formatter modules do not have a set order, and should be designed with this is mind.
The order goes as follows:
Document Preprocessors -> Line Formatters -> Multiline formatters
the document is first run through every specified pre-processor,
then each line passes through the line-formatting pipeline.
while the lines are being formatted, Chandragen listens for the criteria for running a multi-line formatter and runs them if it can.
NOTE: Only one multiline formatter can be active at a time due to architecure limitations

## Configuration
ChandraGen has a heavy focus on configurability. You can specify any number of individual files or directories to process.
ChandraGen configs are formatted using TOML, and have 3 sections:
- defaults
- file
- dir

defaults is where you specify config options that will automatically apply to every file formatted.
you can specify individual files to convert with more granular options by specifying a file config subsection.
dir config subsections will automatically convert every md or mdx file in the input path, and can be made recursive.
dir config entries will simply change the file extension of formatted files to .gmi, preserving the original filename.

any option specified under a file or dir subsection will override the default value, with the exception of the formatter list.
any formatters specified for a subsection will be added to the list of default formatters. to disable a default formatter, it must be added to a subection's formatter_blacklist.
you can get a lit of available formatters from the cli as follows:
`poetry run chandragen list-formatters`
to get specific information about a formatter, use:
`poetry run chandragen formatter-info <formatter_name>`
you can process your completed config with:
`poetry run chandragen run-config <config path>`
All available configuration options can be found in `example_config.toml`

## Extensibility
Chandragen's modular formatter system allows you to write your own formatters and insert them into the pipeline as plugins.
see `chandragen/plugins/example_plugin.py` for all of the boilerplate code and comments guiding you through the process.
Plugin formatters will be registered just like internal ones, and can be listed from the cli.