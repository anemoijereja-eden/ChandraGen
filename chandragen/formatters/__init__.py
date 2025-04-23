from chandragen.plugins import import_all_plugins
from chandragen.types import LineFormatter, MultilineFormatter, DocumentPreprocessor, FormatterRegistry
import importlib
import pkgutil

def import_builtin_formatters():
    for finder, modname, ispkg in pkgutil.iter_modules(__path__):
        full_name = f"{__name__}.{modname}"
        importlib.import_module(full_name)

def build_formatter_registry() -> FormatterRegistry:
    import_all_plugins()
    import_builtin_formatters()
    
    line = {}
    multiline = {}
    preprocessors = {}

    for subclass in LineFormatter.__subclasses__():
        line[subclass.name] = subclass()

    for subclass in MultilineFormatter.__subclasses__():
        multiline[subclass.name] = subclass()

    for subclass in DocumentPreprocessor.__subclasses__():
        preprocessors[subclass.name] = subclass()

    return FormatterRegistry(
        line = line,
        multiline = multiline,
        preprocessor = preprocessors,
    )

FORMATTER_REGISTRY: FormatterRegistry = build_formatter_registry()