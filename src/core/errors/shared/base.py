"""Base exception for shared module errors.

**Feature: shared-modules-refactoring**
**Refactored: Split from exceptions.py for one-class-per-file compliance**
"""

from __future__ import annotations


class SharedModuleError(Exception):
    """Base exception for all shared module errors.

    All custom exceptions in shared modules should inherit from this class
    to enable consistent error handling and filtering.
    """
