"""Confugue, a hierarchical configuration mechanism."""

from confugue.version import __version__

from confugue.confugue import (
    Configuration, configurable, ConfigurationError, ConfigurationWarning, ALL, REQUIRED, logger)
from confugue.interactive_mode import interactive
