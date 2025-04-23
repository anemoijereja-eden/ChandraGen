from chandragen.types import LineFormatter, MultilineFormatter, DocumentPreprocessor, JobConfig as Config, FormatterFlags as Flags

# Plugin loader will load all LineFormatter classes in the plugin directory
# Formatter class MUST provide a name and apply function
class ExampleLineFormattingPlugin(LineFormatter):
    # The name is what the formatter will be referred to as in the registry, and can be placed in the config to invoke the formatter
    name = "example_line_formatting_plugin"
    # Description is used for chandragen CLI documentation features. every formatter is expected to provide a human-readable description here 
    description = """
    Example plugin line formatter:
    
    This line-formatter does nothing.
    it's provided with chandragen to show an example of adding a formatter with a plugin
    """
    valid_types = ["None"]
    # The apply function contains the formatting logic to run.
    # this can be *absolutely anything* so long as it takes a string representing a single line, and returns a string containing a single line. 
    # All formatters MUST be designed under the assumption that the input data will be some mix of an input format and valid gemtext.
    # if a formatter recieves valid gemtext, it should be designed in such a way that it will not destroy that.
    # information about the state of the formatting process is available in the flags.
    def apply(self, line: str, flags: Flags) -> str:
        return line

class ExampleMultilineFormattingPlugin(MultilineFormatter):
    # The name is what the formatter will be referred to as in the registry, and can be placed in the config to invoke the formatter
    name = "example_multiline_formatting_plugin"
    # Description is used for chandragen CLI documentation features. every formatter is expected to provide a human-readable description here 
    description = """
    Example plugin multiline formatter:
    
    This multiline-formatter does nothing.
    it's provided with chandragen to show an example of adding a formatter with a plugin
    """
    valid_types = ["None"]
    # The apply function contains the formatting logic to run.
    # this can be *absolutely anything* so long as it takes a list of lines to format, and returns a list of formatted lines. 
    # All formatters MUST be designed under the assumption that the input data will be some mix of an input format and valid gemtext.
    # if a formatter recieves valid gemtext, it should be designed in such a way that it will not destroy that.
    # information about the state of the formatting process is available in the flags.
    # the config state generated for the formatting job can be pulled from the config object.
    def apply(self, buffer: list, config: Config, flags: Flags) -> list:
        return buffer
    
class ExampleDocumentPreprocessingPlugin(DocumentPreprocessor):
    # The name is what the formatter will be referred to as in the registry, and can be placed in the config to invoke the formatter
    name = "example_document_preprocessing_plugin"
    # Description is used for chandragen CLI documentation features. every formatter is expected to provide a human-readable description here 
    description = """
    Example plugin document preprocessor:
    
    This preprocessor does nothing.
    it's provided with chandragen to show an example of adding a formatter with a plugin
    """
    valid_types = ["None"]

    # The apply function can contain abolutely any formatting logic as long as it takes in a 2d list representing a document to convert,
    # applies some changes to it, and returns the results.
    # Document pre-processors must be designed with the understanding that they are not the only formatter in a pre-processing pipeline.
    # They may recieve some mix of valid gemtext and input format, and must be able to convert the input format without destroying any valid gemtext.
    # Document pre-processors are intended for simple tasks like cutting out and replacing sections of a document.
    # line-formatters and multiline-formatters should be used where possible.
    def apply(self, document, config):
        return document    