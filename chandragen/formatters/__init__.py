import importlib
import pkgutil

from chandragen.plugins import import_all_plugins
from chandragen.types import DocumentPreprocessor, FormatterRegistry, LineFormatter, MultilineFormatter


def import_builtin_formatters():
    for _finder, modname, _ispkg in pkgutil.iter_modules(__path__):
        full_name = f"{__name__}.{modname}"
        importlib.import_module(full_name)

# To avoid import order shenanigans, ensure every module is loaded immediately when the formatter system is initialized
import_all_plugins()
import_builtin_formatters()

def build_formatter_registry() -> FormatterRegistry:
    
    line: dict[str, LineFormatter] = {}
    multiline: dict[str, MultilineFormatter] = {}
    preprocessors: dict[str, DocumentPreprocessor] = {}

    for subclass in LineFormatter.__subclasses__():
        formatter = subclass.create()
        line[formatter.name] = formatter

    for subclass in MultilineFormatter.__subclasses__():
        formatter = subclass.create()
        multiline[formatter.name] = formatter

    for subclass in DocumentPreprocessor.__subclasses__():
        formatter = subclass.create()
        preprocessors[formatter.name] = formatter

    return FormatterRegistry(
        line = line,
        multiline = multiline,
        preprocessor = preprocessors,
    )

FORMATTER_REGISTRY: FormatterRegistry = build_formatter_registry()