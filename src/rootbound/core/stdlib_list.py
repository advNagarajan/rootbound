import sys

def is_stdlib(module_name: str) -> bool:
    # Target Python 3.10+ stdlib lists
    return module_name in sys.builtin_module_names or module_name in getattr(sys, "stdlib_module_names", set())
