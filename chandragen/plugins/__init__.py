import importlib
import pkgutil
import sys

def import_all_plugins():
    current_package = __name__
    current_module = sys.modules[current_package]

    for _, modname, ispkg in pkgutil.iter_modules(current_module.__path__):
        if not ispkg:
            importlib.import_module(f"{current_package}.{modname}")
