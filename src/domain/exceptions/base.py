"""Base domain exception."""


class DomainException(Exception):
    """Base exception for all domain-related errors.

    All domain exceptions should inherit from this class to allow
    for centralized exception handling at the application boundaries.
    """

    pass
