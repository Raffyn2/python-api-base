# ADR-019: Result Pattern Adoption for Error Handling

**Status:** Accepted
**Date:** 2025-01-02
**Author:** Architecture Team
**Supersedes:** N/A
**Replaces:** N/A

---

## Context

### Problem Statement

Traditional exception-based error handling in Python presents several challenges for enterprise applications:

1. **Implicit Control Flow:** Exceptions create invisible control flow paths that are difficult to trace and reason about
2. **Performance Overhead:** Exception creation and stack unwinding can be expensive in high-throughput scenarios
3. **Type Safety:** Exceptions are not part of function signatures, making it hard to know what errors can occur
4. **Error Propagation:** Difficult to track which layers handle which errors without runtime analysis
5. **Testing Complexity:** Need to test both happy path and exception paths separately
6. **Business Logic Mixing:** Business failures (like "user not found") mixed with programming errors (like NullPointerError)

### Current Landscape

The codebase uses multiple error handling approaches:

- **Exceptions:** Used in infrastructure layer (database errors, external service failures)
- **HTTP Status Codes:** Used in interface layer for API responses
- **None Returns:** Used informally in some query handlers
- **Boolean Returns:** Used in some validation functions

This inconsistency makes it difficult to:
- Understand error flow across layers
- Write predictable tests
- Handle errors uniformly
- Reason about failure scenarios

### Requirements

1. **Explicit Error Handling:** Errors should be part of function signatures
2. **Type Safety:** Type system should enforce error handling
3. **Performance:** Minimal overhead for success cases
4. **Composability:** Easy to chain operations and transform results
5. **Backward Compatibility:** Can coexist with existing exception-based code
6. **Developer Experience:** Intuitive API with minimal boilerplate

---

## Decision

We adopt the **Result Pattern** as the primary error handling mechanism for business logic and application layers, while keeping exceptions for infrastructure failures and programming errors.

### Result Pattern Definition

A `Result[T, E]` type that represents either:
- **Success (Ok[T]):** Contains a value of type T
- **Failure (Err[E]):** Contains an error of type E

```python
from typing import TypeVar, Generic, Union
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Ok[T]:
    """Success result containing a value."""
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

@dataclass
class Err[E]:
    """Error result containing an error."""
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> Never:
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default

# Type alias
Result = Ok[T] | Err[E]
```

### Implementation Guidelines

#### 1. Use Result for Business Logic

```python
from core.shared.result import Result, Ok, Err
from domain.users.errors import UserNotFoundError

class GetUserQuery:
    """Query to get user by ID."""

    async def execute(self, user_id: UserId) -> Result[UserDTO, UserNotFoundError]:
        """
        Get user by ID.

        Returns:
            Ok[UserDTO]: User found
            Err[UserNotFoundError]: User not found
        """
        user = await self.repository.find_by_id(user_id)

        if user is None:
            return Err(UserNotFoundError(user_id))

        return Ok(self.mapper.to_dto(user))
```

#### 2. Pattern Matching for Error Handling

```python
# Handler usage
result = await get_user_query.execute(user_id)

match result:
    case Ok(user_dto):
        return Response(status_code=200, content=user_dto)
    case Err(UserNotFoundError(user_id)):
        return Response(status_code=404, content={"error": f"User {user_id} not found"})
```

#### 3. Chainable Operations

```python
from core.shared.result import Result

class UpdateUserCommand:
    """Command to update user."""

    async def execute(self, user_id: UserId, data: UpdateUserDTO) -> Result[UserDTO, DomainError]:
        """
        Update user.

        Returns:
            Ok[UserDTO]: User updated successfully
            Err[UserNotFoundError | ValidationError]: Update failed
        """
        # Chain operations - stop at first error
        return (
            await self._find_user(user_id)
            .and_then(lambda user: self._validate_update(user, data))
            .and_then(lambda user: self._apply_update(user, data))
            .and_then(lambda user: self._save_user(user))
            .map(lambda user: self.mapper.to_dto(user))
        )
```

#### 4. Keep Exceptions for Infrastructure

```python
from sqlalchemy.exc import SQLAlchemyError

class UserRepository:
    """User repository implementation."""

    async def find_by_id(self, user_id: UserId) -> User | None:
        """
        Find user by ID.

        Returns:
            User if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            result = await self.session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            # Infrastructure error - raise exception
            raise DatabaseError(f"Failed to find user: {e}") from e
```

### Layer-Specific Guidelines

| Layer | Use Result For | Use Exceptions For |
|-------|---------------|-------------------|
| **Domain** | Business rule violations | Never (pure functions) |
| **Application** | Use case failures | Never |
| **Infrastructure** | Repository queries | Database errors, network errors |
| **Interface** | Validation errors | Framework errors |

---

## Consequences

### Positive

1. **✅ Explicit Error Handling**
   - Function signatures document possible failures
   - Type checker enforces error handling
   - No hidden control flow

2. **✅ Better Type Safety**
   - Mypy/Pyright can verify all error paths are handled
   - Refactoring is safer (compiler catches missed cases)
   - IDE autocomplete shows possible errors

3. **✅ Improved Testability**
   - Test success and failure paths uniformly
   - No need for `pytest.raises()` context managers
   - Clearer test intent

4. **✅ Performance Benefits**
   - No exception overhead for business failures
   - Faster execution in high-throughput scenarios
   - Reduced GC pressure

5. **✅ Railway-Oriented Programming**
   - Chainable operations with `and_then()`, `map()`, `map_err()`
   - Short-circuit on first error
   - Composable error handling

6. **✅ Better Error Context**
   - Errors are strongly typed domain objects
   - Rich error information without stack traces
   - Easier to serialize for logging/monitoring

### Negative

1. **❌ Learning Curve**
   - Developers need to learn Result pattern
   - Different from traditional Python exception handling
   - Requires understanding of pattern matching

   **Mitigation:**
   - Provide training and documentation
   - Code review guidelines
   - Example implementations

2. **❌ Verbosity**
   - More explicit code (return statements for Ok/Err)
   - Pattern matching can be verbose for simple cases

   **Mitigation:**
   - Helper methods (`unwrap_or()`, `unwrap_or_else()`)
   - Utility functions for common patterns
   - Code generation for repetitive patterns

3. **❌ Mixed Paradigm**
   - Coexists with existing exception-based code
   - Need to convert between Result and exceptions

   **Mitigation:**
   - Clear guidelines on when to use each approach
   - Converter utilities (`result_to_exception()`, `exception_to_result()`)
   - Gradual migration strategy

4. **❌ Limited Library Support**
   - Third-party libraries use exceptions
   - Need adapters/wrappers

   **Mitigation:**
   - Create wrapper utilities for common libraries
   - Document adapter patterns
   - Provide reusable decorators

### Neutral

1. **⚖️ Code Size**
   - More explicit code increases line count
   - But reduces cognitive complexity

2. **⚖️ Stack Traces**
   - No automatic stack traces for business errors
   - But better structured error information

---

## Alternatives Considered

### Alternative 1: Pure Exception-Based

**Description:** Continue using exceptions for all error handling.

**Pros:**
- Standard Python approach
- No learning curve
- Full library support

**Cons:**
- Implicit control flow
- No type safety for errors
- Performance overhead
- Difficult to reason about error propagation

**Why Rejected:** Doesn't address the core problems we're trying to solve (type safety, explicit errors, performance).

---

### Alternative 2: Optional/Maybe Pattern

**Description:** Use `Optional[T]` (or `T | None`) for operations that can fail.

```python
async def find_user(user_id: UserId) -> User | None:
    ...
```

**Pros:**
- Simple to understand
- Built into Python type system
- No additional dependencies

**Cons:**
- No error information (just None)
- Can't distinguish between different failure reasons
- Prone to None-checking boilerplate
- Not composable

**Why Rejected:** Too limited - doesn't carry error information, can't distinguish failure types.

---

### Alternative 3: Either Monad (from returns library)

**Description:** Use the `returns` library which provides `Result`, `Maybe`, `IO` monads.

```python
from returns.result import Result, Success, Failure

async def get_user(user_id: UserId) -> Result[UserDTO, UserNotFoundError]:
    ...
```

**Pros:**
- Battle-tested library
- Full monad implementation
- Rich set of combinators
- Good documentation

**Cons:**
- External dependency
- Heavier learning curve (full functional programming)
- May be overkill for our needs
- Less idiomatic Python

**Why Rejected:** Too heavyweight. We want a simple, lightweight Result pattern without full monadic machinery.

---

### Alternative 4: Union Return Types

**Description:** Return unions of success type and error types.

```python
async def get_user(user_id: UserId) -> UserDTO | UserNotFoundError:
    ...
```

**Pros:**
- No new abstraction
- Type checker support
- Simple to understand

**Cons:**
- Ambiguous (can't tell if error is intended or bug)
- No explicit Success/Error marker
- Less composable
- Harder to distinguish success from error in code

**Why Rejected:** Too ambiguous - can't clearly distinguish between success value and error value.

---

## Migration Strategy

### Phase 1: Foundation (Sprint 1)
- [ ] Implement core Result type
- [ ] Add helper methods (`map`, `and_then`, `unwrap_or`)
- [ ] Create documentation and examples
- [ ] Train development team

### Phase 2: New Code (Sprint 2-3)
- [ ] Use Result for all new use cases
- [ ] Use Result for all new query handlers
- [ ] Use Result for all new command handlers
- [ ] Document patterns in ADR

### Phase 3: Gradual Migration (Sprint 4-6)
- [ ] Migrate critical use cases
- [ ] Migrate frequently-changed modules
- [ ] Add Result to existing query handlers
- [ ] Keep old exception-based code for stability

### Phase 4: Infrastructure Boundaries (Sprint 7-8)
- [ ] Keep exceptions at infrastructure boundaries
- [ ] Convert infrastructure exceptions to Results at application layer
- [ ] Document boundary patterns

---

## Implementation Checklist

- [x] Core Result type implemented (`src/core/shared/result.py`)
- [x] Helper methods implemented
- [x] Pattern matching examples added
- [x] Documentation created
- [ ] Team training conducted
- [ ] Migration guide created
- [ ] Example use cases implemented
- [ ] ADR reviewed and accepted

---

## References

### Internal
- [Code Review 2025](../code-review-comprehensive-2025-01-02.md) - Section on Result Pattern
- [Action Items](../ACTION-ITEMS-2025.md) - Sprint 1 task
- [Executive Summary](../EXECUTIVE-SUMMARY-CODE-REVIEW-2025.md) - Padrões aprovados

### External
- [Railway Oriented Programming](https://fsharpforfunandprofit.com/rop/) - Scott Wlaschin
- [Error Handling in Rust](https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html)
- [Kotlin Result](https://kotlinlang.org/api/latest/jvm/stdlib/kotlin/-result/)
- [Python returns library](https://returns.readthedocs.io/en/latest/)

---

## Examples

### Example 1: Simple Query

```python
from core.shared.result import Result, Ok, Err

class GetItemQuery:
    """Query to get item by ID."""

    async def execute(self, item_id: ItemId) -> Result[ItemDTO, ItemNotFoundError]:
        """Get item by ID."""
        item = await self.repository.find_by_id(item_id)

        if item is None:
            return Err(ItemNotFoundError(item_id))

        return Ok(self.mapper.to_dto(item))

# Usage
result = await query.execute(item_id)

match result:
    case Ok(item):
        return JSONResponse(content=item.model_dump())
    case Err(ItemNotFoundError(id)):
        return JSONResponse(status_code=404, content={"error": f"Item {id} not found"})
```

### Example 2: Command with Multiple Errors

```python
from core.shared.result import Result, Ok, Err

class CreateUserCommand:
    """Command to create user."""

    async def execute(self, data: CreateUserDTO) -> Result[UserDTO, DomainError]:
        """
        Create user.

        Returns:
            Ok[UserDTO]: User created
            Err[ValidationError]: Invalid data
            Err[UserAlreadyExistsError]: User already exists
        """
        # Validate
        validation_result = self._validate(data)
        if validation_result.is_err():
            return validation_result

        # Check if exists
        if await self.repository.exists_by_email(data.email):
            return Err(UserAlreadyExistsError(data.email))

        # Create user
        user = User.create(data.email, data.name)
        await self.repository.save(user)

        return Ok(self.mapper.to_dto(user))

# Usage
result = await command.execute(data)

match result:
    case Ok(user):
        return JSONResponse(status_code=201, content=user.model_dump())
    case Err(ValidationError(errors)):
        return JSONResponse(status_code=400, content={"errors": errors})
    case Err(UserAlreadyExistsError(email)):
        return JSONResponse(status_code=409, content={"error": f"User {email} already exists"})
```

### Example 3: Chaining Operations

```python
class UpdateOrderStatusCommand:
    """Command to update order status."""

    async def execute(
        self,
        order_id: OrderId,
        new_status: OrderStatus,
    ) -> Result[OrderDTO, DomainError]:
        """Update order status."""
        return (
            await self._find_order(order_id)  # Result[Order, OrderNotFoundError]
            .and_then(lambda order: self._validate_transition(order, new_status))  # Result[Order, InvalidStateTransitionError]
            .and_then(lambda order: self._update_status(order, new_status))  # Result[Order, DomainError]
            .and_then(lambda order: self._save_order(order))  # Result[Order, DatabaseError]
            .map(lambda order: self.mapper.to_dto(order))  # Result[OrderDTO, DomainError]
        )
```

---

## Monitoring and Success Criteria

### Metrics

1. **Type Safety**
   - Target: 100% of new use cases use Result
   - Measure: Code review checklist

2. **Error Handling Coverage**
   - Target: All error paths explicitly handled
   - Measure: Mypy strict mode with no `type: ignore`

3. **Developer Satisfaction**
   - Target: 80%+ positive feedback on Result pattern
   - Measure: Developer survey after Sprint 3

4. **Performance**
   - Target: No performance regression
   - Measure: Benchmark use case execution time

### Review Schedule

- **1 month:** Review adoption rate and developer feedback
- **3 months:** Assess migration progress and adjust strategy
- **6 months:** Full evaluation - continue, modify, or deprecate

---

## Appendix

### A. Result Implementation

Location: `src/core/shared/result.py`

Key methods:
- `is_ok() -> bool`
- `is_err() -> bool`
- `unwrap() -> T`
- `unwrap_or(default: T) -> T`
- `map(fn: Callable[[T], U]) -> Result[U, E]`
- `map_err(fn: Callable[[E], F]) -> Result[T, F]`
- `and_then(fn: Callable[[T], Result[U, E]]) -> Result[U, E]`

### B. Error Hierarchy

```
DomainError (base)
├── ValidationError
│   ├── InvalidEmailError
│   ├── InvalidPasswordError
│   └── InvalidFieldError
├── NotFoundError
│   ├── UserNotFoundError
│   ├── ItemNotFoundError
│   └── OrderNotFoundError
├── ConflictError
│   ├── UserAlreadyExistsError
│   └── ResourceAlreadyExistsError
└── BusinessRuleError
    ├── InvalidStateTransitionError
    └── InsufficientPermissionsError
```

### C. Conversion Utilities

```python
def result_to_exception[T, E](result: Result[T, E]) -> T:
    """Convert Result to value or raise exception."""
    match result:
        case Ok(value):
            return value
        case Err(error):
            raise DomainException(error)

def exception_to_result[T](fn: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    """Decorator to convert exceptions to Result."""
    def wrapper(*args, **kwargs) -> Result[T, Exception]:
        try:
            return Ok(fn(*args, **kwargs))
        except Exception as e:
            return Err(e)
    return wrapper
```

---

**Last Updated:** 2025-01-02
**Next Review:** 2025-04-01
**Status:** Accepted ✅
