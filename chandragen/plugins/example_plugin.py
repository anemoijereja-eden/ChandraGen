from chandragen.formatters.registry import (
    register_line_formatter,
    register_multiline_formatter,
    register_preprocessor,
)
from chandragen.formatters.types import (
    DocumentPreprocessor,
    FormatterConfig,
    FormatterFlags,
    LineFormatter,
    MultilineFormatter,
)


# Plugin loader will load all LineFormatter classes in the plugin directory
# Formatter class MUST provide a name and apply function
@register_line_formatter
class ExampleLineFormattingPlugin(LineFormatter):
    def __init__(self):
        # The name is what the formatter will be referred to as in the registry, and can be placed in the config to invoke the formatter
        # Description is used for chandragen CLI documentation features. every formatter is expected to provide a human-readable description here
        super().__init__(
            "example_line_formatting_plugin",
            """
    Example plugin line formatter:
    
    This line-formatter does nothing.
    it's provided with chandragen to show an example of adding a formatter with a plugin
            """,
            ["None"],
        )

    # Boilerplate method needed for the plugin class to load properly
    @classmethod
    def create(cls) -> LineFormatter:
        return cls()

    # The apply function contains the formatting logic to run.
    # this can be *absolutely anything* so long as it takes a string representing a single line, and returns a string containing a single line.
    # All formatters MUST be designed under the assumption that the input data will be some mix of an input format and valid gemtext.
    # if a formatter recieves valid gemtext, it should be designed in such a way that it will not destroy that.
    # information about the state of the formatting process is available in the flags.
    def apply(self, line: str, flags: FormatterFlags) -> str:
        return line


@register_multiline_formatter
class ExampleMultilineFormattingPlugin(MultilineFormatter):
    def __init__(self):
        # The name is what the formatter will be referred to as in the registry, and can be placed in the config to invoke the formatter
        # Description is used for chandragen CLI documentation features. every formatter is expected to provide a human-readable description here
        super().__init__(
            "example_multiline_formatting_plugin",
            """
    Example plugin multiline formatter:
    
    This multiline-formatter does nothing.
    it's provided with chandragen to show an example of adding a formatter with a plugin
            """,
            ["None"],
            "start regex",
            "end regex",
        )

    @classmethod
    def create(cls) -> MultilineFormatter:
        return cls()

    # The apply function contains the formatting logic to run.
    # this can be *absolutely anything* so long as it takes a list of lines to format, and returns a list of formatted lines.
    # All formatters MUST be designed under the assumption that the input data will be some mix of an input format and valid gemtext.
    # if a formatter recieves valid gemtext, it should be designed in such a way that it will not destroy that.
    # information about the state of the formatting process is available in the flags.
    # the config state generated for the formatting job can be pulled from the config object.
    def apply(self, buffer: list[str], config: FormatterConfig, flags: FormatterFlags) -> list[str]:
        return buffer


@register_preprocessor
class ExampleDocumentPreprocessingPlugin(DocumentPreprocessor):
    def __init__(self):
        # Takes 3 arguments:
        # The name is what the formatter will be referred to as in the registry, and can be placed in the config to invoke the formatter
        # Description is used for chandragen CLI documentation features. every formatter is expected to provide a human-readable description here
        # valid_types is a list of file extensions the plugin is designed to handle.
        super().__init__(
            "example_document_preprocessing_plugin",
            """
    Example plugin document preprocessor:
    
    This preprocessor does nothing.
    it's provided with chandragen to show an example of adding a formatter with a plugin
        """,
            ["None"],
        )

    @classmethod
    def create(cls) -> DocumentPreprocessor:
        return cls()

    # The apply function can contain abolutely any formatting logic as long as it takes in a 2d list representing a document to convert,
    # applies some changes to it, and returns the results.
    # Document pre-processors must be designed with the understanding that they are not the only formatter in a pre-processing pipeline.
    # They may recieve some mix of valid gemtext and input format, and must be able to convert the input format without destroying any valid gemtext.
    # Document pre-processors are intended for simple tasks like cutting out and replacing sections of a document.
    # line-formatters and multiline-formatters should be used where possible.
    def apply(self, document: list[str], config: FormatterConfig):
        return document

