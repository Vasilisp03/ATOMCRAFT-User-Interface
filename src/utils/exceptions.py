"""Custom exceptions for the AtomCraft system."""


class AtomCraftException(Exception):
    """Base exception for all AtomCraft-related errors."""
    pass


class NetworkException(AtomCraftException):
    """Raised when network communication fails."""
    pass


class HardwareException(AtomCraftException):
    """Raised when hardware interface operations fail."""
    pass


class DataProcessingException(AtomCraftException):
    """Raised when data processing operations fail."""
    pass


class ConfigurationException(AtomCraftException):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseException(AtomCraftException):
    """Raised when database operations fail."""
    pass
