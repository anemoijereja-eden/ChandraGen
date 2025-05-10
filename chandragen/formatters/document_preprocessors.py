from loguru import logger

from chandragen.formatters.types import DocumentPreprocessor
from chandragen.formatters.types import FormatterConfig as Config

# document pre-processors
# formatters that make changes to the document before running it through the pipeline

class StripHeading(DocumentPreprocessor):
    def __init__(self):
        super().__init__(
        name = "strip_heading",
        description = """
    Strip Heading
    
    Removes a section of the document from the top down to a specified line,
    then inserts a preformatted heading in its place
        """,
        valid_types = ["md", "mdx"],
        )
    
    @classmethod
    def create(cls) -> DocumentPreprocessor:
        return cls()
   
    def apply(self, document: list[str], config: Config) -> list[str]:
        if config.heading is None or config.heading_end_pattern is None:
            logger.warning("Cannot strip heading without defined replacement and ending pattern")
            return document
        heading_end = document.index(config.heading_end_pattern) + config.heading_strip_offset
        del document[0:heading_end]
        heading = config.heading.splitlines(keepends=True)
        return heading + document

class StripFooting(DocumentPreprocessor):
    def __init__(self):
        super().__init__(
        name = "strip_footing",
        description = """
    Strip Footing
    
    Removes a section of the document from a specified line to the bottom,
    then inserts a preformatted footer in its place
        """,
        valid_types = ["md", "mdx"],
        )
    
    @classmethod
    def create(cls) -> DocumentPreprocessor:
        return cls()

    def apply(self, document: list[str], config: Config) -> list[str]:
        if config.footing is None or config.footing_start_pattern is None:
            logger.warning("cannot strip footing without defined replacement and starting pattern")
            return document
        footer_start = document.index(config.footing_start_pattern) + config.footing_strip_offset
        del document[footer_start:]
        footer = config.footing.splitlines(keepends=True)
        document.extend(footer)
        return document

class ConvertFrontmatter(DocumentPreprocessor):
    def __init__(self):
        super().__init__(
            "convert_frontmatter",
            """
            Convert Frontmatter
            
            Converts the frontmatter in a markdown or mdx document to a gemini-friendly heading and footing
            """,
            ["md", "mdx"]
        )
    
    @classmethod
    def create(cls) -> DocumentPreprocessor:
        return cls()
    
    def apply(self, document: list[str], config: Config) -> list[str]:
        if not document[0].startswith("---"):
            # This document doesn't have a frontmatter, leave as-is.
            return document
        
        frontmatter: dict[str, str] = {}
        stripped_document: list[str] | None = None
        
        for index, line in enumerate(document[1:]):
            if not line.startswith("---"):
                key, value = line.strip().split(":")
                frontmatter[key.strip().strip("'").strip('"')] = value.strip().strip("'").strip('"')
            else:
                stripped_document = document[2+index:]
                break
            
        if stripped_document is None:
            logger.warning("Frontmatter conversion failed!! Frontmatter does not terminate")
            return document
        
        if "date" in frontmatter:
            try:
                by = frontmatter["author"]
            except KeyError:
                by = ""
            stripped_document.append(f"""
{"-"*20}
Written {by} on {frontmatter["date"]}
            """)
        
        if "title" in frontmatter:
            try:
                subtitle = frontmatter["description"]
            except KeyError:
                subtitle = ""
            header = f"""
# {frontmatter["title"]}
{subtitle}
{"-"*20}\n
"""
            return [header, *stripped_document]
        return stripped_document