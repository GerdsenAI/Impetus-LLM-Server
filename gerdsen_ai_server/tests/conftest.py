"""
Test configuration — align module namespaces for mock.patch compatibility.

create_app() registers blueprints via gerdsen_ai_server.src.routes.* paths,
but tests patch src.routes.* paths. This conftest ensures both paths resolve
to the same Python module object in sys.modules.
"""

import sys


def pytest_configure(config):
    """Alias gerdsen_ai_server.src.* modules to src.* in sys.modules."""
    # Trigger module loading by importing create_app (which registers blueprints)
    from src.main import create_app  # noqa: F401

    # Eagerly import modules that are lazily loaded inside route handlers
    # so they appear in sys.modules for aliasing
    try:
        import gerdsen_ai_server.src.model_loaders.mlx_loader  # noqa: F401
    except Exception:
        pass

    # Alias long-form module paths to short-form so patches work.
    # Always overwrite to ensure both paths reference the same module object.
    for name, mod in list(sys.modules.items()):
        if name.startswith("gerdsen_ai_server.src."):
            short_name = name.replace("gerdsen_ai_server.", "", 1)
            sys.modules[short_name] = mod
