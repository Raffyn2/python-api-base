"""Script to refactor large Python files into packages.

**Feature: file-size-compliance-phase2**
**Validates: Requirements 1-6**

Usage:
    python scripts/refactor_to_package.py src/my_api/shared/query_analyzer.py
"""

import ast
import re
import sys
from pathlib import Path
from typing import Any


def extract_module_parts(source: str) -> dict[str, list[str]]:
    """Extract different parts of a module for splitting."""
    tree = ast.parse(source)
    
    parts: dict[str, list[str]] = {
        "imports": [],
        "enums": [],
        "models": [],
        "config": [],
        "service": [],
        "other": [],
    }
    
    lines = source.splitlines()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno - 1
            end = node.end_lineno or start + 1
            class_source = "\n".join(lines[start:end])
            
            # Categorize by class type
            if "Enum" in [base.id for base in node.bases if isinstance(base, ast.Name)]:
                parts["enums"].append((node.name, class_source))
            elif "Config" in node.name or "Settings" in node.name:
                parts["config"].append((node.name, class_source))
            elif any(d.id == "dataclass" for d in node.decorator_list if isinstance(d, ast.Name)):
                parts["models"].append((node.name, class_source))
            elif "Service" in node.name or "Manager" in node.name:
                parts["service"].append((node.name, class_source))
            else:
                parts["other"].append((node.name, class_source))
    
    return parts


def get_public_symbols(source: str) -> list[str]:
    """Extract public symbols from __all__ or module-level definitions."""
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
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                symbols.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                symbols.append(node.name)
    
    return symbols


def create_init_file(package_dir: Path, symbols: list[str], docstring: str) -> None:
    """Create __init__.py with re-exports."""
    # Group symbols by likely module
    init_content = f'''"""{docstring}

**Feature: file-size-compliance-phase2**
**Validates: Requirements 5.1, 5.2, 5.3**
"""

# Re-exports for backward compatibility
__all__ = {sorted(symbols)!r}
'''
    
    (package_dir / "__init__.py").write_text(init_content)


def refactor_file(file_path: Path) -> None:
    """Refactor a single file into a package."""
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    source = file_path.read_text(encoding="utf-8")
    module_name = file_path.stem
    package_dir = file_path.parent / module_name
    
    # Create package directory
    package_dir.mkdir(exist_ok=True)
    
    # Get public symbols
    symbols = get_public_symbols(source)
    
    # Extract docstring
    tree = ast.parse(source)
    docstring = ast.get_docstring(tree) or f"{module_name} module"
    
    # Create __init__.py
    create_init_file(package_dir, symbols, docstring)
    
    print(f"Created package: {package_dir}")
    print(f"Symbols: {symbols}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python refactor_to_package.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    refactor_file(file_path)
