import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path


def import_all_plugins():
    current_package = __name__
    current_module = sys.modules[current_package]

    for _, modname, ispkg in pkgutil.iter_modules(current_module.__path__):
        if not ispkg:
            importlib.import_module(f"{current_package}.{modname}")
    external_plugins_path = Path("/plugins")
    if external_plugins_path.exists():
        sys.path.insert(0, str(external_plugins_path))  # Add to importable path

        for plugin_file in external_plugins_path.glob("*.py"):
            if plugin_file.name == "__init__.py":
                continue  # skip __init__.py
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)       