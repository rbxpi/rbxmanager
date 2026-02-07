#!/usr/bin/env python3

""" RbxPI Install Manager

RbxPI Install Manager makes it easy to install RbxPI in your Roblox projects.
The project is developed primarily in Python.
"""

import pathlib
import argparse
import logging
import os
from argparse import ArgumentParser

try:  # 2.7+
    from logging.config import dictConfig
except ImportError as err:
    raise ImportError(f"Unable to import the needed for logging."
                      f"Check that your Python version is 2.7 or later.\n\n{err}")

from __init__ import __version__
from common.pypixz import install_package, PackageInstallationError, install_requirements
from common._os import os_compatibility, get_os_name
from common.environment import python_compatibility
from common.github_release import get_latest_version

logger = logging.getLogger("main")

try:
    import yaml
except ModuleNotFoundError as err:
    if input("The pyyaml package is not installed, would you like to try installing it automatically?"
             "\n[Y/n] : ").lower() in ['y', '']:
        try:
            install_package(
                package='pyyaml',
                logger=logger
            )
            exit("pyyaml has been successfully installed, please restart rbxmanager.")
        except PackageInstallationError as error:
            exit(logger.error("Please try installing pyyaml manually."))
    else:
        exit(1)


def get_rbxmanager_path() -> pathlib.Path:
    current_file = pathlib.Path(__file__).resolve()
    rbxmanager_path_default = current_file.parent

    return rbxmanager_path_default


RBXMANAGER_PATH_DEFAULT = get_rbxmanager_path()

LOGGING_CONFIG_PATH = f"{RBXMANAGER_PATH_DEFAULT}/configs/logging.yaml"
LOGS_DIRECTORY = f"{RBXMANAGER_PATH_DEFAULT}/{pathlib.Path("cache/logs")}"
REQUIREMENTS_FILE = f"requirements.txt"


def argparse_setup() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """ Configure the argparse module

    This function create configuration and `argparse.ArgumentParser` object
    to manage the program's launch arguments.

    :return: a tuple containing the parsed arguments.
    :rtype: tuple[argparse.ArgumentParser, argparse.Namespace]
    """

    parser = argparse.ArgumentParser(description=f"RbxPI Install Manager - v{__version__}")
    parser.add_argument('-v', '--verbose', action='store_true', help="show detailed output and progress information")
    parser.add_argument('-f', '--force', nargs='+', choices=['os', 'python', 'deps', 'all'], help="skip specific validation steps")
    parser.add_argument('-u', '--update', action='store_true', help="check if an update is available")
    parser.add_argument('--debug', action='store_true', help="enable debug output")

    args = parser.parse_args()
    return parser, args


def logging_setup(args: argparse.Namespace) -> None:
    """ Configure the logging system based on the passed arguments.

    This function initializes and adapts the behavior of the main logger based
    on the options and information provided.

    :param args: The parsed command line arguments
    :type args: Namespace

    :rtype: None
    """

    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.verbose:
        logger.setLevel(logging.INFO)

    logger.info("Configuring the logging system.")

    for handler in logger.handlers:
        if getattr(handler, "baseFilename", "").endswith("debug.log"):
            handler.addFilter(lambda record: record.levelno == logging.DEBUG)

    logger.info("Logging system successfully configured.")

    return None


def force_steps_check(args: argparse.Namespace, parser: ArgumentParser) -> bool:
    """ Checks the compatibility of the execution environment based on the
    provided command-line options.

    This function runs a series of checks (operating system, Python
    environment, required packages) unless specific checks have been explicitly
    excluded using the `--skip-check` argument.
    The order and logic of all checks are defined in an internal dictionary,
    allowing centralized and maintainable control over compatibility tests.

    :arg args: The parsed command line arguments.
    :type args: {argparse.Namespace}

    :arg parser: The parser instance used to raise argument-related errors.
    :type parser: {argparse.Namespace}

    :return: Returns True only when the user explicitly passes `--skip-check all`,
    meaning that no compatibility checks are executed. Otherwise, the function returns
    True and simply runs the required checks.
    :rtype: bool
    """

    steps = {
        "os": {
            "name": "Operating system",
            "function": lambda : os_compatibility()
        },
        "python": {
            "name": "Python environment",
            "function": lambda : python_compatibility()
        },
        "deps": {
            "name": "Packages",
            "function": lambda : install_requirements(REQUIREMENTS_FILE, logger)
        }
    }

    steps_passed = args.force or []
    if 'all' in steps_passed:
        if steps_passed and (len(steps_passed) > 1 or steps_passed[0] != 'all'):
            logger.error("The 'all' argument must be the first and only choice after '-f'/'--force'.")
            parser.error("The 'all' argument must be the first and only choice after '-f'/'--force'.")
        return True

    for index, value in steps.items():
        if index not in steps_passed:
            logger.info(f"Running {value['name']} compatibility check.")
            value['function']()
            logger.info(f"{value['name']} compatibility check successful!")
        else:
            logger.warning(f"Skipping {value['name']} compatibility check.")

    return True


def main():
    parser, args = argparse_setup()

    os.makedirs(name=LOGS_DIRECTORY, exist_ok=True)
    with open(LOGGING_CONFIG_PATH, 'r') as file:
        logging_config = yaml.safe_load(file)

    dictConfig(logging_config)
    logging_setup(args)

    if args.update:
        latest_version = get_latest_version(__version__)
        if latest_version:
            print(latest_version)
        exit(1)

    force_steps_check(args, parser)

    from core import RbxManager
    RbxManager(__version__, get_os_name(), args)

if __name__ == '__main__':
    main()
