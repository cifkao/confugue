import threading
from typing import Any
import os


thread_local = threading.local()
thread_local.mode = None


def get_interactive_mode() -> str:
    if thread_local.mode is not None:
        return thread_local.mode

    mode = os.environ.get('CONFUGUE_INTERACTIVE', None)
    if not mode:
        mode = 'none'
    if mode not in ['all', 'missing', 'none']:
        mode = 'all'
    return mode


class interactive:
    """A context manager that enables or disables the interactive editing mode.

    Args:
        mode: `'all'` to edit all values, `'missing'` to edit only missing values, or
            `'none'` to disable the interactive mode.
    """

    def __init__(self, mode: str = 'all'):
        if mode not in ['all', 'missing', 'none']:
            raise ValueError('Invalid mode: {!r}'.format(mode))
        self.mode = mode
        self._orig_mode = None

    def __enter__(self) -> None:
        self._orig_mode = thread_local.mode
        thread_local.mode = self.mode

    def __exit__(self, e_type: Any, e_value: Any, e_traceback: Any) -> None:
        thread_local.mode = self._orig_mode
        self._orig_mode = None
