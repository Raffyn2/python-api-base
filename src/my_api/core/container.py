"""Dependency injection container using dependency-injector."""

import logging
from collections.abc import Callable
from typing import Any

from dependency_injector import containers, providers

from my_api.core.config import Settings

logger = logging.getLogger(__name__)


class Container(containers.DeclarativeContainer):
    """Application DI container.

    Manages all application dependencies including configuration,
    database sessions, repositories, mappers, and use cases.
    """

    wiring_config = containers.WiringConfiguration(
        modules=[
            "my_api.adapters.api.routes.items",
            "my_api.adapters.api.routes.health",
        ]
    )

    # Configuration
    config = providers.Singleton(Settings)

    # Database session manager - configured at runtime via app.state.db
    # This is a Dependency provider that will be set during app startup
    db_session_manager = providers.Dependency()


class LifecycleManager:
    """Manages application lifecycle hooks for startup and shutdown.

    Provides a centralized way to register and execute startup/shutdown
    callbacks for resources like database connections, caches, etc.
    """

    def __init__(self) -> None:
        """Initialize lifecycle manager."""
        self._startup_hooks: list[Callable[[], Any]] = []
        self._shutdown_hooks: list[Callable[[], Any]] = []
        self._async_startup_hooks: list[Callable[[], Any]] = []
        self._async_shutdown_hooks: list[Callable[[], Any]] = []

    def on_startup(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register a synchronous startup hook.

        Args:
            func: Function to call on startup.

        Returns:
            The registered function (for decorator use).
        """
        self._startup_hooks.append(func)
        return func

    def on_shutdown(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register a synchronous shutdown hook.

        Args:
            func: Function to call on shutdown.

        Returns:
            The registered function (for decorator use).
        """
        self._shutdown_hooks.append(func)
        return func

    def on_startup_async(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register an async startup hook.

        Args:
            func: Async function to call on startup.

        Returns:
            The registered function (for decorator use).
        """
        self._async_startup_hooks.append(func)
        return func

    def on_shutdown_async(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Register an async shutdown hook.

        Args:
            func: Async function to call on shutdown.

        Returns:
            The registered function (for decorator use).
        """
        self._async_shutdown_hooks.append(func)
        return func

    def run_startup(self) -> None:
        """Execute all synchronous startup hooks."""
        for hook in self._startup_hooks:
            try:
                logger.info(f"Running startup hook: {hook.__name__}")
                hook()
            except Exception as e:
                logger.error(f"Startup hook {hook.__name__} failed: {e}")
                raise

    def run_shutdown(self) -> None:
        """Execute all synchronous shutdown hooks in reverse order."""
        for hook in reversed(self._shutdown_hooks):
            try:
                logger.info(f"Running shutdown hook: {hook.__name__}")
                hook()
            except Exception as e:
                logger.error(f"Shutdown hook {hook.__name__} failed: {e}")

    async def run_startup_async(self) -> None:
        """Execute all async startup hooks."""
        for hook in self._async_startup_hooks:
            try:
                logger.info(f"Running async startup hook: {hook.__name__}")
                await hook()
            except Exception as e:
                logger.error(f"Async startup hook {hook.__name__} failed: {e}")
                raise

    async def run_shutdown_async(self) -> None:
        """Execute all async shutdown hooks in reverse order."""
        for hook in reversed(self._async_shutdown_hooks):
            try:
                logger.info(f"Running async shutdown hook: {hook.__name__}")
                await hook()
            except Exception as e:
                logger.error(f"Async shutdown hook {hook.__name__} failed: {e}")


# Global lifecycle manager instance
lifecycle = LifecycleManager()


def create_container(settings: Settings | None = None) -> Container:
    """Create and configure the DI container.

    Args:
        settings: Optional settings override.

    Returns:
        Container: Configured DI container.
    """
    container = Container()

    if settings:
        container.config.override(providers.Object(settings))

    return container
