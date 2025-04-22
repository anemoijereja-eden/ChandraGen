import re
from abc import ABC, abstractmethod
from chandragen.types import FormatterFlags as Flags

#Line Formatter base class
class LineFormatter(ABC):
    name: str
    
    @abstractmethod
    def apply(self, line: str, flags: Flags) -> str:
        pass
    
# Internal line formatters:

#Markdown Converters
class StripInlineMarkdown(LineFormatter):
    name = "strip_inline_formatting"
    
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

    def apply(self, line: str, flags: Flags) -> str:
        return line if not line.startswith("```") else "```\n"

# MDX Converters
class StripImportsExports(LineFormatter):
    name = "strip_imports_exports"
    
    def apply(self, line: str, flags: Flags) -> str:
        if line.strip().startswith(("import ", "export ")):
            return ""
        return line

class StripJSXTags(LineFormatter):
    name = "strip_jsx_tags"
    
    def apply(self, line: str, flags: Flags) -> str:
        if line.strip().startswith("<") and not line.strip().startswith(("<!--", "<!DOCTYPE")):
            return ""
        return line

class StripJSXExpressions(LineFormatter):
    name = "strip_jsx_expressions"
    
    def apply(self, line: str, flags: Flags) -> str:
        return re.sub(r"{.*?}", "", line)

class ConvertKnownMDXComponents(LineFormatter):
    name = "convert_known_mdx_components"
    
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


def build_formatter_registry() -> dict[str, LineFormatter]:
    registry = {}
    for subclass in LineFormatter.__subclasses__():
        if hasattr(subclass, "name") and subclass.name:
            registry[subclass.name] = subclass()
    return registry

FORMATTER_REGISTRY = build_formatter_registry()