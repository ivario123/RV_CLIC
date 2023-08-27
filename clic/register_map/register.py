"""
Defines a generic register class.

Different types of registers:

    - Read-only
    - Write-only
    - Read-write
    - WARL (Write-Any-Read-Legal) i.e. read-write but only certain values are legal
    and thus illegal values are ignored.
"""

from enum import Enum, auto
from typing import Callable

from clic import Elaboratable, Module, Signal
from . import decorators
