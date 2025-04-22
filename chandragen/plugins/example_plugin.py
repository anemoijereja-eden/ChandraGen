from chandragen.line_formatters import LineFormatter
from chandragen.types import FormatterFlags as Flags

# Plugin loader will load all LineFormatter classes in the plugin directory
# Formatter class MUST provide a name and apply function
class ExampleLineFormattingPlugin(LineFormatter):
    # The name is what the formatter will be referred to as in the registry, and can be placed in the config to invoke the formatter
    name = "example_line_formatting_plugin"
    
    # The apply function contains the formatting logic to run.
    # this can be *absolutely anything* so long as it takes a string representing a single line, and returns a string containing a single line. 
    # All formatters MUST be deisgned under the assumption that the input data will be some mix of an input format and valid gemtext.
    # if a formatter recieves valid gemtext, it should be designed in such a way that it will not destroy that.
    # information about the state of the formatting process is available in the flags.
    def apply(self, line: str, flags: Flags) -> str:
        return line