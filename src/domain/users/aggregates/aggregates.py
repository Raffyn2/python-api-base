"""User aggregate root for the Users bounded context.

**Feature: architecture-restructuring-2025**
**Validates: Requirements 2.4**
"""

from datetime import datetime
from typing import Self

from pydantic import Field

from core.base.domain.aggregate_root import AggregateRoot
from domain.users.events import (
    UserDeactivatedEvent,
    UserEmailChangedEvent,
    UserEmailVerifiedEvent,
    UserLoggedInEvent,
    UserPasswordChangedEvent,
    UserProfileUpdatedEvent,
    UserReactivatedEvent,
    UserRegisteredEvent,
)
from domain.users.value_objects import Email


class UserAggregate(AggregateRoot[str]):
    """User aggregate root.

    The User aggregate is the entry point for all user-related operations.
    It ensures consistency of user data and emits domain events.
    """

    email: str = Field(..., description="User email address")
    password_hash: str = Field(..., description="Hashed password")
    username: str | None = Field(default=None, description="Optional username")
    display_name: str | None = Field(default=None, description="Display name")
    is_active: bool = Field(default=True, description="Whether user is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")
    last_login_at: datetime | None = Field(default=None, description="Last login timestamp")

    @classmethod
    def create(
        cls,
        user_id: str,
        email: str,
        password_hash: str,
        username: str | None = None,
        display_name: str | None = None,
    ) -> Self:
        """Factory method to create a new user.

        Args:
            user_id: Unique user identifier.
            email: User email address.
            password_hash: Hashed password.
            username: Optional username.
            display_name: Optional display name.

        Returns:
            New UserAggregate instance with UserRegisteredEvent.
        """
        # Validate email format
        email_vo = Email.create(email)

        user = cls(
            id=user_id,
            email=email_vo.value,
            password_hash=password_hash,
            username=username,
            display_name=display_name,
        )

        # Emit registration event
        user.add_event(
            UserRegisteredEvent(
                user_id=user_id,
                email=email_vo.value,
            )
        )

        return user

    def change_email(self, new_email: str) -> None:
        """Change user email address.

        Args:
            new_email: New email address.
        """
        # Validate new email
        email_vo = Email.create(new_email)
        old_email = self.email

        object.__setattr__(self, "email", email_vo.value)
        object.__setattr__(self, "is_verified", False)
        self.mark_updated()
        self.increment_version()

        self.add_event(
            UserEmailChangedEvent(
                user_id=str(self.id),
                old_email=old_email,
                new_email=email_vo.value,
            )
        )

    def change_password(self, new_password_hash: str) -> None:
        """Change user password.

        Args:
            new_password_hash: New hashed password.
        """
        object.__setattr__(self, "password_hash", new_password_hash)
        self.mark_updated()
        self.increment_version()

        self.add_event(UserPasswordChangedEvent(user_id=str(self.id)))

    def verify_email(self) -> None:
        """Mark email as verified."""
        object.__setattr__(self, "is_verified", True)
        self.mark_updated()

        self.add_event(UserEmailVerifiedEvent(user_id=str(self.id), email=self.email))

    def deactivate(self, reason: str = "") -> None:
        """Deactivate the user account.

        Args:
            reason: Reason for deactivation.
        """
        object.__setattr__(self, "is_active", False)
        self.mark_updated()
        self.increment_version()

        self.add_event(
            UserDeactivatedEvent(
                user_id=str(self.id),
                reason=reason,
            )
        )

    def reactivate(self) -> None:
        """Reactivate the user account."""
        object.__setattr__(self, "is_active", True)
        self.mark_updated()
        self.increment_version()

        self.add_event(UserReactivatedEvent(user_id=str(self.id)))

    def record_login(
        self,
        login_time: datetime,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Record a successful login.

        Args:
            login_time: Time of login.
            ip_address: Client IP address (optional).
            user_agent: Client user agent (optional).
        """
        object.__setattr__(self, "last_login_at", login_time)
        self.mark_updated()

        self.add_event(
            UserLoggedInEvent(
                user_id=str(self.id),
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

    def update_profile(
        self,
        username: str | None = None,
        display_name: str | None = None,
    ) -> None:
        """Update user profile information.

        Args:
            username: New username (if provided).
            display_name: New display name (if provided).
        """
        changed_fields: list[str] = []

        if username is not None and username != self.username:
            object.__setattr__(self, "username", username)
            changed_fields.append("username")
        if display_name is not None and display_name != self.display_name:
            object.__setattr__(self, "display_name", display_name)
            changed_fields.append("display_name")

        if changed_fields:
            self.mark_updated()
            self.increment_version()
            self.add_event(
                UserProfileUpdatedEvent(
                    user_id=str(self.id),
                    changed_fields=tuple(changed_fields),
                )
            )
