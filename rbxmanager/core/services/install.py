#!/usr/bin/env python3

import logging
import os
import pathlib
import shutil

from .shared import Shared
from core.shell import Shell

logger = logging.getLogger("main")

ROJO_ENV = {"rojo", "r"}
ROBLOX_STUDIO_ENV = {"roblox studio", "robloxstudio", "rs"}

class Install:
    """ Handle the installation process of RbxPI components

    This class manages the workflow for selecting a release version,
    defining the target environment, and executing the download of
    necessary assets.
    """

    def __init__(self) -> None:
        self.release = None
        self.environment = None
        self.install_dir = None

        logger.debug("Initializing install process instance.")
        logger.info("Starting installation workflow")

        self.select_release()
        self.select_environment()
        self.install()

    def select_release(self) -> None:
        """ Prompt the user to select a specific release version

        This function displays available releases, captures user input,
        and validates that the selected version exists in the database.

        :return: None
        :rtype: NoneType
        """

        releases = Shared.get_release()
        print("Choose a version of RbxPI")

        user_input = Shell.input()
        release = Shared.release_validation_verification(releases, user_input)

        if not release:
            logger.error(f"Invalid version selected '{user_input}'")
            exit(1)

        self.release = release
        logger.debug(f"User selected release: {self.release.get('tag')}")

    def select_environment(self) -> None:
        """ Handle the environment selection process

        This function asks the user to choose between Rojo or Roblox Studio
        and updates the instance state if the choice is valid.

        :return: None
        :rtype: NoneType
        """

        print("\nChoose your environment")
        choice = Shell.input("[Rojo / Roblox Studio]").lower()

        if choice in ROJO_ENV or choice in ROBLOX_STUDIO_ENV:
            self.environment = choice
            logger.debug(f"Environment set to: {self.environment}")
        else:
            logger.error(f"Invalid environment choice: '{choice}'")

    def install(self) -> None:
        """ Route the installation logic based on the chosen environment

        This function triggers the specific installation sub-routine (Rojo or
        Roblox Studio) according to the user's previous selection.

        :return: None
        :rtype: NoneType
        """

        if self.environment in ROBLOX_STUDIO_ENV:
            logger.info("Routing to Roblox Studio installation path.")
            self.install_roblox_studio()
        elif self.environment in ROJO_ENV:
            logger.info("Routing to Rojo installation path.")
            self.install_rojo()
        else:
            logger.error(f"Unsupported environment: {self.environment}")
            exit(1)

    def install_roblox_studio(self) -> None:
        """ Execute the installation workflow for Roblox Studio

        This function fetches the direct download URL for the .rbxm asset,
        downloads it, and notifies the user of its final location.

        :return: None
        :rtype: NoneType
        """

        url = self.get_rbxm_download_url()
        logger.info(f"Downloading .rbxm asset for {self.release.get('tag')}...")

        full_path = self.download(url)

        logger.info(f"Installation successful. Asset saved to {full_path}")
        print(f"Installation complete, the .rbxm file is located in: {full_path}")

    def install_rojo(self) -> None:
        """ Execute the installation workflow for a Rojo project

        This function downloads the source archive, extracts it to a temporary
        directory, moves the core files to the project directory, and cleans
        up the extracted folder.

        :return: None
        :rtype: NoneType
        """

        self.install_dir = self.ask_install_directory()

        print(f"\nDo you want to install RbxPI {self.release.get("tag")}?")
        if Shell.input("[Y/n]").lower() in ["y", ""]:
            tag = self.release["tag"]
            url = f"https://github.com/rbxpi/rbxpi-core/archive/refs/tags/{tag}.zip"

            logger.info(f"Downloading source archive for {tag}...")
            archive_path = self.download(url)

            try:
                logger.info("Extracting and deploying files...")
                extracted_folder = Shared.extract_file(archive_path, self.install_dir)

                source = os.path.join(self.install_dir, extracted_folder, "src", "RbxPI")
                destination = os.path.join(self.install_dir, "RbxPI")

                if os.path.exists(destination):
                    logger.error(f"Installation aborted: Destination already exists at {destination}")
                    exit(1)

                logger.debug(f"Copying tree from {source} to {destination}")
                shutil.copytree(source, destination)

                logger.debug(f"Cleaning up temporary folder: {extracted_folder}")
                shutil.rmtree(os.path.join(self.install_dir, extracted_folder))

                logger.info(f"Rojo installation completed at {destination}")
                print(f"Rojo installation completed at {destination}")

            except Exception as err:
                logger.error(f"An error occurred during Rojo installation: {err}")
                exit(1)

    def get_rbxm_download_url(self) -> str:
        """ Identify and construct the download URL for the .rbxm asset

        This function parses the release asset list to find the binary Roblox
        model file and generates its GitHub release download link.

        :return: The formatted download URL for the asset.
        :rtype: str
        """

        tag = self.release.get("tag")
        assets = self.release.get("assets", [])

        logger.debug(f"Searching for .rbxm in assets: {assets}")

        asset = next((a for a in assets if a.endswith(".rbxm")), None)

        if not asset:
            logger.warning(f"No .rbxm asset found for release {tag}")
            exit(1)

        return f"https://github.com/rbxpi/rbxpi-core/releases/download/{tag}/{asset}"

    @staticmethod
    def ask_install_directory() -> str:
        """ Request an absolute installation path from the user

        This function captures a path via the shell and validates that
        it corresponds to an existing directory on the system.

        :return: The validated absolute path to the directory.
        :rtype: str
        """

        print("\nEnter the absolute path to the directory where you want\nto install RbxPI in your project.")
        path = os.path.abspath(Shell.input())

        if not os.path.isdir(path):
            logger.error(f"Absolute path entered invalid: {path}")
            exit(1)

        logger.debug(f"Install directory validated: {path}")
        return path

    @staticmethod
    def download(url: str) -> pathlib.Path:
        """ Handle file download via the Shared utility

        This function acts as a wrapper for the shared download logic,
        logging the process and ensuring the path is valid before proceeding.

        :arg url: The URL of the file to be downloaded.
        :type url: str

        :return: The local path of the downloaded file.
        :rtype: str
        """

        logger.debug(f"Target download URL: {url}")
        _, path = Shared.download_file(url)

        if not path:
            logger.error("Installation failed during file download.")
            exit(1)

        return path
