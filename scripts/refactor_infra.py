"""Refactor infrastructure modules."""

import ast
import shutil
from pathlib import Path


def get_all_symbols(source: str) -> list[str]:
    tree = ast.parse(source)
    symbols = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                symbols.append(elt.value)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            if node.name not in symbols:
                symbols.append(node.name)
        elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            if node.name not in symbols:
                symbols.append(node.name)
    return sorted(set(symbols))


def get_docstring(source: str) -> str:
    tree = ast.parse(source)
    return ast.get_docstring(tree) or ""


def refactor_module(base_dir: str, name: str) -> bool:
    base = Path(base_dir)
    file_path = base / f"{name}.py"
    if not file_path.exists():
        print(f"SKIP: {name} (not found)")
        return False

    source = file_path.read_text(encoding="utf-8")
    symbols = get_all_symbols(source)
    docstring = get_docstring(source)

    pkg_dir = base / name
    pkg_dir.mkdir(exist_ok=True)

    core_path = pkg_dir / "core.py"
    shutil.copy(file_path, core_path)

    short_doc = docstring[:200] if docstring else f"{name} module"
    init_content = f'''"""
{short_doc}

Feature: file-size-compliance-phase2
Validates: Requirements 5.1, 5.2, 5.3
"""

from .core import *

__all__ = {symbols!r}
'''
    (pkg_dir / "__init__.py").write_text(init_content, encoding="utf-8")
    file_path.unlink()
    print(f"OK: {name} -> {len(symbols)} symbols")
    return True


if __name__ == "__main__":
    # Infrastructure modules
    refactor_module("src/my_api/infrastructure/auth", "token_store")
    refactor_module("src/my_api/infrastructure/observability", "telemetry")
    
    # Adapter modules
    refactor_module("src/my_api/adapters/api/websocket", "types")
    refactor_module("src/my_api/adapters/api/routes", "auth")
