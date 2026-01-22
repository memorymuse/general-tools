"""Sample Python file for testing."""
from typing import Optional
import os


class Calculator:
    """A simple calculator class."""

    def __init__(self, precision: int = 2):
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return round(a + b, self.precision)

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return round(a - b, self.precision)


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


async def async_operation(value: int) -> int:
    """An async operation."""
    return value * 2
