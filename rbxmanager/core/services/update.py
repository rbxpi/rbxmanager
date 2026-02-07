#!/usr/bin/env python3

import os
import logging
import pathlib
import shutil

from core.shell import Shell
from .shared import Shared

logger = logging.getLogger("main")


class Update:
    """ Manage the update process for Rojo-based RbxPI installations

    This class handles identifying the current version, selecting a target
    release, and performing the file replacement to update the core components.
    """

    def __init__(self):
        self.install_dir = None
        self.old_release = None
        self.new_release = None

        print("\n* Please note that this action is only valid for installations via Rojo.")

        logger.debug("Starting Update process initialization")

        self.select_install_dir()
        self.get_old_release()
        self.select_release()

        print(f"\nDo you want to update RbxPI from {self.old_release} to {self.new_release.get("tag")}?")
        if Shell.input("[Y/n]").lower() in ["y", ""]:
            tag = self.new_release["tag"]
            url = f"https://github.com/rbxpi/rbxpi-core/archive/refs/tags/{tag}.zip"

            logger.info(f"Updating RbxPI: {self.old_release} -> {tag}")
            archive_path = self.download(url)

            try:
                logger.debug(f"Removing old installation directory: {self.install_dir}/RbxPI")
                shutil.rmtree(f"{self.install_dir}/RbxPI")

                logger.info("Extracting update archive...")
                extracted_folder = Shared.extract_file(archive_path, self.install_dir)

                source = os.path.join(self.install_dir, extracted_folder, "src", "RbxPI")
                destination = os.path.join(self.install_dir, "RbxPI")

                if os.path.exists(destination):
                    logger.error(f"Destination already exists and cannot be overwritten: {destination}")
                    exit(1)

                logger.info(f"Deploying new files to {destination}")
                shutil.copytree(source, destination)

                logger.debug(f"Cleaning up extraction folder: {extracted_folder}")
                shutil.rmtree(os.path.join(self.install_dir, extracted_folder))

                logger.info("RbxPI update completed successfully.")
                print("RbxPI update completed successfully.")

            except Exception as err:
                logger.error(f"An error occurred during file manipulation: {err}")
                exit(1)

    def select_install_dir(self) -> None:
        """ Prompt the user for the RbxPI installation directory

        This function validates that the provided path is a directory and
        contains an existing RbxPI installation.

        :return: None
        :rtype: NoneType
        """

        print("\nEnter the absolute directory of RbxPI (do not include the 'RbxPI' folder in it)")
        path = os.path.abspath(Shell.input())

        if not os.path.isdir(path):
            logger.error(f"Invalid directory path: {path}")
            exit(1)
        elif not os.path.exists(f"{path}/RbxPI/"):
            logger.error(f"RbxPI installation not found in: {path}")
            exit(1)

        self.install_dir = path
        logger.debug(f"Installation directory validated: {self.install_dir}")

    def get_old_release(self) -> None:
        """ Extract the current version from the local installation

        This function reads the `Version.txt` file located in the RbxPI
        folder to determine the currently installed version tag.

        :return: None
        :rtype: NoneType
        """

        version_file = f"{self.install_dir}/RbxPI/Version.txt"

        if not os.path.isfile(version_file):
            logger.error(f"Version.txt missing in {self.install_dir}/RbxPI/")
            self.old_release = "unknown"
            return

        with open(version_file, "r", encoding="utf-8") as file:
            version = file.read(5)

        self.old_release = f"v{version}"
        logger.debug(f"Current local version detected: {self.old_release}")

    def select_release(self) -> None:
        """ Handle the selection of the target update version

        This function displays the current version, lists available releases
        via the database, and validates the user's choice for the update.

        :return: None
        :rtype: NoneType
        """

        print("\n* If you install a version lower than the one you currently have,\nsome features or packages may not be supported.")

        releases = Shared.get_release()

        print(f"* Your current version of RbxPI is {self.old_release}")
        print("\nChoose a version of RbxPI")

        user_input = Shell.input()
        release = Shared.release_validation_verification(releases, user_input)

        if not release:
            logger.error(f"User selected an invalid or non-existent version: '{user_input}'")
            exit(1)

        self.new_release = release
        logger.debug(f"Target update version: {self.new_release.get('tag')}")

    @staticmethod
    def download(url: str) -> pathlib.Path:
        """ Handle file download via the Shared utility

        This function acts as a wrapper for the shared download logic,
        logging the process and ensuring the path is valid before proceeding.

        :arg url: The URL of the file to be downloaded.
        :type url: str

        :return: The local path of the downloaded file.
        :rtype: pathlib.Path
        """

        logger.debug(f"Requesting download from URL: {url}")
        _, path = Shared.download_file(url)

        if not path:
            logger.error(f"Failed to download update from {url}")
            exit(1)

        return path
