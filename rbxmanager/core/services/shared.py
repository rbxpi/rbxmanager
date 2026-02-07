#!/usr/bin/env python

import logging
import os
import requests
from pathlib import Path
import zipfile

from core.database import Database
from core.shell import Shell

logger = logging.getLogger("main")


class Shared:
    """ Provide shared utility methods for release management and file handling

    This class serves as a helper to coordinate database interactions,
    validate release versions, and manage file downloads to the system.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_release() -> dict:
        """ Retrieve and synchronize the list of available releases

        This function ensures the database exists, checks if the data is stale
        (older than 7 days) or empty, and triggers a remote fetch if necessary
        before displaying the content.

        :return: A dictionary containing the release information.
        :rtype: dict
        """

        if not Database.exist():
            logger.info("Database not found. Initializing a new one.")
            Database.create()

        content = Database.get()
        days_since_modification = Database.get_days_since_modification()

        if content == {} or days_since_modification >= 7:
            logger.info(
                msg="Database is empty. Fetching data from remote..." if content == {} else f"Database is "
                                                                                            f"{days_since_modification} "
                                                                                            f"days old. Auto-updating..."
            )
            Database.fetch_releases()
            content = Database.get()
        else:
            logger.debug(f"Using cached database (age: {days_since_modification} days).")

        Database.show()
        return content

    @staticmethod
    def release_validation_verification(content: dict, release: str) -> dict | bool:
        """ Verify if a specific release tag exists within the provided data

        This function iterates through the release dictionary to find a match
        for the specified version tag.

        :arg content: The dictionary of releases to search through.
        :type content: dict

        :arg release: The version tag to validate.
        :type release: str

        :return: The release data if found, False otherwise.
        :rtype: dict | bool
        """

        logger.debug(f"Validating release tag: '{release}'")

        for index in content:
            if content[index]['tag'] == release:
                logger.debug(f"Release '{release}' found in database.")
                return content[index]

        logger.warning(f"Release tag '{release}' not found in the database.")
        return False

    @staticmethod
    def download_file(url: str, filename: str | None = None) -> tuple[bool, Path | None]:
        """ Download a file from a URL to the user's downloads directory

        This function identifies the appropriate local downloads folder,
        streams the file content from the web, and saves it to the disk.

        :param url: The direct link to the file to download.
        :type url: str

        :param filename: Optional custom name for the file (defaults to URL name).
        :type filename: str | None

        :return: A tuple containing the success status and the file path.
        :rtype: tuple[bool, Path | None]
        """

        if not filename:
            filename = url.split("/")[-1]

        if os.path.exists(Path.home() / "Téléchargements"):
            downloads_dir = Path.home() / "Téléchargements"
        else:
            downloads_dir = Path.home() / "Downloads"

        full_path = downloads_dir / filename

        logger.info(f"Starting download: {filename}")
        logger.debug(f"Download URL {url} | Destination: {full_path}")

        try:
            response = requests.get(url, stream=True, timeout=15)
            response.raise_for_status()

            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Successfully downloaded: {filename}")
            return True, full_path

        except requests.exceptions.RequestException as err:
            logger.error(f"Network error while downloading {filename}: {err}")
            return False, None

        except IOError as err:
            logger.error(f"Disk error while saving {filename}: {err}")
            return False, None

    @staticmethod
    def extract_file(file_path, destination):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            folder_name = zip_ref.namelist()[0].split('/')[0]
            zip_ref.extractall(destination)

        return folder_name
