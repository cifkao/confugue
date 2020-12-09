import os
import subprocess
import sys
import tempfile
import traceback
from typing import Any

import yaml


def edit_yaml(content: str) -> Any:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = os.path.join(tmpdir, 'config.yaml')
        while True:
            with open(tmp, 'w') as f:
                f.write(content)

            proc = subprocess.run([detect_editor(), tmp], check=False)
            if proc.returncode == 0:
                with open(tmp) as f:
                    content = f.read()

                try:
                    return yaml.load(content, Loader=yaml.Loader)
                except yaml.YAMLError:
                    traceback.print_exc()

            if input('Editing failed; retry [y/N]? ').lower() != 'y':
                raise EditError()


def detect_editor() -> str:
    for key in ['VISUAL', 'EDITOR']:
        if os.environ.get(key):
            return os.environ[key]

    if sys.platform.startswith('win'):
        return 'notepad'

    for editor in ['sensible-editor', 'nano', 'vim']:
        proc = subprocess.run(
            ['which', editor], stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=False)
        if proc.returncode == 0:
            return editor

    return 'vi'


class EditError(Exception):
    pass
