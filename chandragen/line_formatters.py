import re
from abc import ABC, abstractmethod
from chandragen.types import FormatterFlags as Flags
from chandragen.plugins import import_all_plugins
#Line Formatter base class
class LineFormatter(ABC):
    name: str
    description: str
    valid_types: list[str]
    
    @abstractmethod
    def apply(self, line: str, flags: Flags) -> str:
        pass
    
# Internal line formatters:

#Markdown Converters
class StripInlineMarkdown(LineFormatter):
    name = "strip_inline_md_formatting"
    description = """
    Strip inline markdown formatting:
    
    Strips all inline markdown bold and italic sequences
    naive approach, may cause issues.
    does not affect preformatted text/codeblocks
    """
    valid_types = ["md", "mdx"]
    
    def apply(self, line: str, flags: Flags) -> str:
        if flags.in_preformat:
            return line
        #set up a regex method to remove inline markdown
        inline_md_replacements = {"*":"","**":"","***":"","_":"","__":"","___":"",}
        inline_md_pattern = re.compile("|".join(re.escape(old) for old in inline_md_replacements))
        # regex it all out
        return f"{line[0:2]}{inline_md_pattern.sub(lambda match: inline_md_replacements[match.group(0)], line[2:])}"

class ConvertBulletPointLinks(LineFormatter):
    name = "convert_bullet_point_links"
    description = """
    Convert Bullet Point Links
    
    takes markdown style links immediately following a bullet point,
    and converts them into a gemini link-line.
    """
    valid_types = ["md", "mdx"] 
    
    def apply(self, line: str, flags: Flags) -> str:
        #Convert "- [label](url)" markdown link lines to "=> url label" gemtext links
        if line.startswith("- ["):
            # strip the first 3 characters "- [" off the line, then break it in half at the ](
            link = line[3:].split("](")
            # Since we have to flip the fields around, we also need to strip the newline and add one at the end.
            return f"=> {link[1].replace(")\n","")} {link[0]}\n"
        return line

class NormalizeCodeBlocks(LineFormatter):
    name = "normalize_code_blocks"
    description="""
    Normalize codeblocks
    
    Strip out any characters defining a language on a code-block
    ensures compatibility with the gemini preformatted text block standard.
    """
    valid_types = ["md", "mdx"]

    def apply(self, line: str, flags: Flags) -> str:
        return line if not line.startswith("```") else "```\n"

# MDX Converters
class StripImportsExports(LineFormatter):
    name = "strip_imports_exports"
    description = """
    Strip Imports and Exports
    
    Remove the line if it's a JSX import or export.
    """
    valid_types = ["mdx"]
    
    def apply(self, line: str, flags: Flags) -> str:
        if line.strip().startswith(("import ", "export ")):
            return ""
        return line

class StripJSXTags(LineFormatter):
    name = "strip_jsx_tags"
    description = """
    Strip JSX Tags
    
    Naively remove lines starting with < that aren't DOCTYPE or HTML style comments.
    This should also remove some HTML tags, but not very well.
    """
    valid_types = ["mdx"]
    
    def apply(self, line: str, flags: Flags) -> str:
        if line.strip().startswith("<") and not line.strip().startswith(("<!--", "<!DOCTYPE")):
            return ""
        return line

class StripJSXExpressions(LineFormatter):
    name = "strip_jsx_expressions"
    description = """
    Strip JSX expressions
    
    Naively strips out anything enclosed by curly braces.
    This will probably break your site.
    If you want to substitute them properly, set up a plugin formatter that does so, see the plugin example :3
    """
    valid_types = ["mdx"]
    def apply(self, line: str, flags: Flags) -> str:
        return re.sub(r"{.*?}", "", line)

class ConvertKnownMDXComponents(LineFormatter):
    name = "convert_known_mdx_components"
    description = """
    Convert Known MDX components
    
    If a line is an MDX note or warning, replace with a basic NOTE: or WARNING:
    """
    valid_types = ["mdx"]
    def apply(self, line: str, flags: Flags) -> str:
        component_map = {
            "<Note>": "NOTE:",
            "</Note>": "",
            "<Warning>": "WARNING:",
            "</Warning>": ""
        }
        for jsx, gem in component_map.items():
            line = line.replace(jsx, gem)
        return line

# Load all plugins, then use introspection to build the formatter registry
def build_formatter_registry() -> dict[str, LineFormatter]:
    import_all_plugins()
    registry = {}
    for subclass in LineFormatter.__subclasses__():
        if hasattr(subclass, "name") and subclass.name:
            registry[subclass.name] = subclass()
    return registry

FORMATTER_REGISTRY = build_formatter_registry()