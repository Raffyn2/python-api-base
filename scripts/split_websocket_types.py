"""Split websocket types service.py into smaller modules."""

from pathlib import Path

# Read the file
path = Path("src/my_api/adapters/api/websocket/types/service.py")
content = path.read_text()
lines = content.splitlines()

# Find class boundaries
import ast
tree = ast.parse(content)

classes = []
for node in ast.iter_child_nodes(tree):
    if isinstance(node, ast.ClassDef):
        start = node.lineno - 1
        if node.decorator_list:
            start = node.decorator_list[0].lineno - 1
        end = node.end_lineno
        classes.append((node.name, start, end))

print(f"Found {len(classes)} classes:")
for name, start, end in classes:
    print(f"  {name}: lines {start+1}-{end}")

# Get imports (first 20 lines approximately)
imports_end = classes[0][1] if classes else 20
imports = "\n".join(lines[:imports_end])

# Split: messages (first 3 classes), manager (rest)
messages_classes = classes[:3]
manager_classes = classes[3:]

# Build messages.py
messages_content = f'''"""WebSocket message types.

Feature: file-size-compliance-phase2
"""

{imports}

'''
for name, start, end in messages_classes:
    messages_content += "\n".join(lines[start:end]) + "\n\n"

# Build manager.py
manager_content = f'''"""WebSocket connection manager and routes.

Feature: file-size-compliance-phase2
"""

{imports}
from .messages import WebSocketMessage, SystemMessage, ErrorMessage

'''
for name, start, end in manager_classes:
    manager_content += "\n".join(lines[start:end]) + "\n\n"

# Write files
pkg = Path("src/my_api/adapters/api/websocket/types")
(pkg / "messages.py").write_text(messages_content)
(pkg / "manager.py").write_text(manager_content)

# Remove old service.py
(pkg / "service.py").unlink()

# Update __init__.py
init_content = '''"""WebSocket types and connection management.

Feature: file-size-compliance-phase2
"""

from .messages import ErrorMessage, SystemMessage, WebSocketMessage
from .manager import ConnectionManager, WebSocketRoute

__all__ = [
    "ConnectionManager",
    "ErrorMessage",
    "SystemMessage",
    "WebSocketMessage",
    "WebSocketRoute",
]
'''
(pkg / "__init__.py").write_text(init_content)

print("\nOK: websocket/types split into messages.py, manager.py")
for f in pkg.glob("*.py"):
    print(f"  {f.name}: {len(f.read_text().splitlines())} lines")
