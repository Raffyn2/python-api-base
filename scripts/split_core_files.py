"""Split core.py files into smaller modules.

Feature: file-size-compliance-phase2
"""

import ast
import re
from pathlib import Path
from typing import Any


def get_imports(source: str) -> str:
    """Extract import statements from source."""
    tree = ast.parse(source)
    lines = source.splitlines()
    imports = []
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno - 1
            end = node.end_lineno or start + 1
            imports.append("\n".join(lines[start:end]))
    
    return "\n".join(imports)


def get_node_source(source: str, node: ast.AST) -> str:
    """Get source code for a node including decorators."""
    lines = source.splitlines()
    start = node.lineno - 1
    
    # Include decorators
    if hasattr(node, "decorator_list") and node.decorator_list:
        start = node.decorator_list[0].lineno - 1
    
    end = node.end_lineno or start + 1
    return "\n".join(lines[start:end])


def categorize_nodes(source: str) -> dict[str, list[tuple[str, str]]]:
    """Categorize top-level nodes by type."""
    tree = ast.parse(source)
    categories: dict[str, list[tuple[str, str]]] = {
        "enums": [],
        "models": [],
        "config": [],
        "service": [],
        "constants": [],
        "functions": [],
    }
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            node_source = get_node_source(source, node)
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
            
            if "Enum" in bases:
                categories["enums"].append((node.name, node_source))
            elif any(d.id == "dataclass" for d in node.decorator_list if isinstance(d, ast.Name)):
                if "Config" in node.name or "Settings" in node.name:
                    categories["config"].append((node.name, node_source))
                else:
                    categories["models"].append((node.name, node_source))
            elif "Config" in node.name or "Settings" in node.name or "Builder" in node.name:
                categories["config"].append((node.name, node_source))
            elif "Service" in node.name or "Manager" in node.name or "Handler" in node.name:
                categories["service"].append((node.name, node_source))
            else:
                categories["service"].append((node.name, node_source))
        
        elif isinstance(node, ast.FunctionDef):
            node_source = get_node_source(source, node)
            categories["functions"].append((node.name, node_source))
        
        elif isinstance(node, ast.Assign):
            lines = source.splitlines()
            start = node.lineno - 1
            end = node.end_lineno or start + 1
            node_source = "\n".join(lines[start:end])
            
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    categories["constants"].append((target.id, node_source))
    
    return categories


def split_core_file(pkg_dir: Path) -> bool:
    """Split a core.py file into smaller modules."""
    core_path = pkg_dir / "core.py"
    if not core_path.exists():
        return False
    
    source = core_path.read_text(encoding="utf-8")
    lines = len(source.splitlines())
    
    if lines <= 400:
        print(f"SKIP: {pkg_dir.name} ({lines} lines, already compliant)")
        return False
    
    imports = get_imports(source)
    categories = categorize_nodes(source)
    
    # Get docstring
    tree = ast.parse(source)
    docstring = ast.get_docstring(tree) or f"{pkg_dir.name} module"
    
    # Create module files
    created_modules = []
    all_symbols = []
    
    # Enums module
    if categories["enums"]:
        content = f'"""{pkg_dir.name} enums."""\n\n{imports}\n\n'
        for name, src in categories["enums"]:
            content += f"\n{src}\n"
            all_symbols.append(name)
        (pkg_dir / "enums.py").write_text(content, encoding="utf-8")
        created_modules.append("enums")
    
    # Models module
    if categories["models"]:
        content = f'"""{pkg_dir.name} models."""\n\n{imports}\n'
        if categories["enums"]:
            enum_names = ", ".join(n for n, _ in categories["enums"])
            content += f"from .enums import {enum_names}\n"
        content += "\n"
        for name, src in categories["models"]:
            content += f"\n{src}\n"
            all_symbols.append(name)
        (pkg_dir / "models.py").write_text(content, encoding="utf-8")
        created_modules.append("models")
    
    # Config module
    if categories["config"]:
        content = f'"""{pkg_dir.name} configuration."""\n\n{imports}\n'
        if categories["enums"]:
            enum_names = ", ".join(n for n, _ in categories["enums"])
            content += f"from .enums import {enum_names}\n"
        if categories["models"]:
            model_names = ", ".join(n for n, _ in categories["models"])
            content += f"from .models import {model_names}\n"
        content += "\n"
        for name, src in categories["config"]:
            content += f"\n{src}\n"
            all_symbols.append(name)
        (pkg_dir / "config.py").write_text(content, encoding="utf-8")
        created_modules.append("config")
    
    # Constants module
    if categories["constants"]:
        content = f'"""{pkg_dir.name} constants."""\n\n'
        for name, src in categories["constants"]:
            content += f"{src}\n"
            all_symbols.append(name)
        (pkg_dir / "constants.py").write_text(content, encoding="utf-8")
        created_modules.append("constants")
    
    # Service module (main logic)
    if categories["service"] or categories["functions"]:
        content = f'"""{pkg_dir.name} service."""\n\n{imports}\n'
        if categories["enums"]:
            enum_names = ", ".join(n for n, _ in categories["enums"])
            content += f"from .enums import {enum_names}\n"
        if categories["models"]:
            model_names = ", ".join(n for n, _ in categories["models"])
            content += f"from .models import {model_names}\n"
        if categories["config"]:
            config_names = ", ".join(n for n, _ in categories["config"])
            content += f"from .config import {config_names}\n"
        if categories["constants"]:
            const_names = ", ".join(n for n, _ in categories["constants"])
            content += f"from .constants import {const_names}\n"
        content += "\n"
        for name, src in categories["service"]:
            content += f"\n{src}\n"
            all_symbols.append(name)
        for name, src in categories["functions"]:
            content += f"\n{src}\n"
            all_symbols.append(name)
        (pkg_dir / "service.py").write_text(content, encoding="utf-8")
        created_modules.append("service")
    
    # Update __init__.py
    init_content = f'"""{docstring[:200]}\n\nFeature: file-size-compliance-phase2\n"""\n\n'
    for mod in created_modules:
        init_content += f"from .{mod} import *\n"
    init_content += f"\n__all__ = {sorted(set(all_symbols))!r}\n"
    (pkg_dir / "__init__.py").write_text(init_content, encoding="utf-8")
    
    # Remove core.py
    core_path.unlink()
    
    print(f"OK: {pkg_dir.name} -> {len(created_modules)} modules, {len(all_symbols)} symbols")
    return True


def main():
    """Main entry point."""
    packages = [
        "src/my_api/shared/query_analyzer",
        "src/my_api/shared/protocols",
        "src/my_api/shared/multitenancy",
        "src/my_api/shared/background_tasks",
        "src/my_api/shared/http2_config",
        "src/my_api/shared/connection_pool",
        "src/my_api/shared/memory_profiler",
        "src/my_api/shared/bff",
        "src/my_api/shared/request_signing",
        "src/my_api/shared/feature_flags",
        "src/my_api/shared/streaming",
        "src/my_api/shared/api_composition",
        "src/my_api/shared/response_transformation",
        "src/my_api/shared/mutation_testing",
        "src/my_api/shared/graphql_federation",
        "src/my_api/infrastructure/auth/token_store",
        "src/my_api/infrastructure/observability/telemetry",
        "src/my_api/adapters/api/websocket/types",
        "src/my_api/adapters/api/routes/auth",
    ]
    
    success = 0
    for pkg in packages:
        pkg_path = Path(pkg)
        if pkg_path.exists() and split_core_file(pkg_path):
            success += 1
    
    print(f"\nSplit {success} packages")


if __name__ == "__main__":
    main()
