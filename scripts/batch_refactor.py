"""Batch refactor shared modules to packages.

**Feature: file-size-compliance-phase2**
"""

import ast
import shutil
from pathlib import Path


def get_all_symbols(source: str) -> list[str]:
    """Extract public symbols from module."""
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
    """Extract module docstring."""
    tree = ast.parse(source)
    return ast.get_docstring(tree) or ""


def refactor_module(shared_dir: Path, name: str) -> bool:
    """Refactor a single module to package."""
    file_path = shared_dir / f"{name}.py"
    if not file_path.exists():
        print(f"SKIP: {name} (already refactored)")
        return False

    source = file_path.read_text(encoding="utf-8")
    symbols = get_all_symbols(source)
    docstring = get_docstring(source)

    # Create package dir
    pkg_dir = shared_dir / name
    pkg_dir.mkdir(exist_ok=True)

    # Move original file to core.py
    core_path = pkg_dir / "core.py"
    shutil.copy(file_path, core_path)

    # Create __init__.py with re-exports
    short_doc = docstring[:200] if docstring else f"{name} module"
    init_content = f'''"""{short_doc}

Feature: file-size-compliance-phase2
Validates: Requirements 5.1, 5.2, 5.3
"""

from .core import *

__all__ = {symbols!r}
'''
    (pkg_dir / "__init__.py").write_text(init_content, encoding="utf-8")

    # Remove original file
    file_path.unlink()

    print(f"OK: {name} -> {len(symbols)} symbols")
    return True


def main():
    """Main entry point."""
    files = [
        "query_analyzer", "protocols", "multitenancy", "background_tasks",
        "http2_config", "connection_pool", "memory_profiler", "bff",
        "request_signing", "feature_flags", "streaming", "api_composition",
        "response_transformation", "mutation_testing", "graphql_federation"
    ]

    shared_dir = Path("src/my_api/shared")
    
    success = 0
    for name in files:
        if refactor_module(shared_dir, name):
            success += 1
    
    print(f"\nRefactored {success}/{len(files)} modules")


if __name__ == "__main__":
    main()
