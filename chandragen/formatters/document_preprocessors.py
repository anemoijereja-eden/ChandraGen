from chandragen.types import DocumentPreprocessor, JobConfig as Config

# document pre-processors
# formatters that make changes to the document before running it through the pipeline

class StripHeading(DocumentPreprocessor):
    name = "strip_heading"
    description = """
    Strip Heading
    
    Removes a section of the document from the top down to a specified line,
    then inserts a preformatted heading in its place
    """
    valid_types = ["md", "mdx"]

    def apply(self, document: list, config: Config) -> list:
        if config.heading is None or config.heading_end_pattern is None:
            print("Error! cannot strip heading without defined replacement and ending pattern")
            return document
        heading_end = document.index(config.heading_end_pattern) + config.heading_strip_offset
        del document[0:heading_end]
        heading = config.heading.splitlines(keepends=True)
        document = heading + document
        return document

class StripFooting(DocumentPreprocessor):
    name = "strip_footing"
    description = """
    Strip Footing
    
    Removes a section of the document from a specified line to the bottom,
    then inserts a preformatted footer in its place
    """
    valid_types = ["md", "mdx"]
    
    def apply(self, document: list, config: Config) -> list:
        if config.footing is None or config.footing_start_pattern is None:
            print("Error! cannot strip footing without defined replacement and starting pattern")
            return document
        footer_start = document.index(config.footing_start_pattern) + config.footing_strip_offset
        del document[footer_start:]
        footer = config.footing.splitlines(keepends=True)
        document.extend(footer)
        return document


