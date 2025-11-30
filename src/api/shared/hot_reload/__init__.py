"""Hot Reload Middleware - Automatic code reload in development.

**Feature: file-size-compliance-phase2, Task 2.2**
**Validates: Requirements 1.2, 5.1, 5.2, 5.3**

Provides:
- File system watching for code changes
- Automatic module reloading without server restart
- Configurable watch patterns and ignore patterns
- Development-only middleware with safety checks
"""

from .enums import FileChangeType, ReloadStrategy
from .handler import ModuleReloader
from .middleware import HotReloadMiddleware, create_hot_reload_middleware
from .models import FileChange, ReloadResult, WatchConfig
from .watcher import FileHasher, FileWatcher

__all__ = [
    "FileChange",
    "FileChangeType",
    "FileHasher",
    "FileWatcher",
    "HotReloadMiddleware",
    "ModuleReloader",
    "ReloadResult",
    "ReloadStrategy",
    "WatchConfig",
    "create_hot_reload_middleware",
]
