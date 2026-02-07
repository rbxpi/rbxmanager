#!/user/bin/env python3

import os
import subprocess


def clear_screen() -> int:
    """Clear the terminal screen.

    Clears the console output by using the appropriate system command
    depending on the operating system (``cls`` for Windows, ``clear`` for
    Unix/Linux/Mac).

    :return: the return code of the executed system command.
    :rtype: int
    """

    return subprocess.call(f"{'cls' if os.name == 'nt' else 'clear'}", shell=False)
