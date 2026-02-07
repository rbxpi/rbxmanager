#!/usr/bin/env python3

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests

SRC_DIRECTORY = os.path.abspath("rbxmanager")
DATA_FILE = Path(f"{SRC_DIRECTORY}/cache/data.json")
RBXPI_REPO_API = "https://api.github.com/repos/rbxpi/rbxpi-core/releases"

logger = logging.getLogger("main")

class Database:
    """ Manage the local JSON database storage

    This class provides static methods to handle the creation,
    existence check, reading, and writing of the application's cache data.
    """

    def __init__(self):
        pass

    @staticmethod
    def create() -> None:
        """ Create the database file if it does not exist

        This function checks for the presence of the data file and
        initializes it with an empty JSON object if missing.

        :return: None
        :rtype: NoneType
        """

        if not os.path.exists(DATA_FILE):
            logger.info(f"Initializing new database file at: {DATA_FILE}")

            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            with open(DATA_FILE, "w") as json_file:
                json.dump({}, json_file)
        else:
            logger.debug(f"Database file already exists. Skipping creation.")

        return None

    @staticmethod
    def exist() -> bool:
        """ Check if the database file exists

        This function verifies the physical existence of the JSON cache file.

        :return: True if the file exists, False otherwise.
        :rtype: bool
        """

        exists = os.path.exists(DATA_FILE)
        logger.debug(f"Checking database existence: {exists} ({DATA_FILE})")

        return exists

    @staticmethod
    def write(data: dict | list) -> None:
        """ Write data to the database file

        This function saves a dictionary or list into the JSON file
        with specific formatting for UTF-8 support and indentation.

        :arg data: The data to be stored in the file.
        :type data: dict | list

        :return: None
        :rtype: NoneType
        """

        logger.info("Saving data to database...")
        logger.debug(f"Writing {len(data)} items to {DATA_FILE}")

        try:
            with open(DATA_FILE, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)

            logger.debug("Write operation successful.")

        except Exception as err:
            logger.error(f"Failed to write to database: {err}")
            raise

        return None

    @staticmethod
    def get() -> dict | list:
        """ Retrieve data from the database file

        This function reads the content of the JSON file and parses it
        into a Python object.

        :return: The data stored in the JSON file.
        :rtype: dict | list
        """

        logger.debug(f"Loading data from {DATA_FILE}")

        try:
            with open(DATA_FILE, "r") as json_file:
                data = json.load(json_file)
                logger.debug(f"Successfully loaded {len(data)} items.")
                return data

        except json.JSONDecodeError as err:
            logger.error(f"Database file is corrupted: {err}")
            return {}

        except FileNotFoundError:
            logger.warning(f"Database file not found during read: {DATA_FILE}")
            return {}

    @staticmethod
    def get_days_since_modification() -> int | None:
        """ Calculate the number of days since the database was last modified

        This function retrieves the last modification timestamp of the data file
        and calculates the difference in days relative to the current UTC time.

        :return: The number of days since modification, or None if the file doesn't exist.
        :rtype: int | None
        """

        if not os.path.exists(DATA_FILE):
            logger.debug(f"Modification check skipped: {DATA_FILE} does not exist.")
            return None

        modification_time = DATA_FILE.stat().st_mtime

        dt_modification = datetime.fromtimestamp(modification_time, tz=timezone.utc)
        dt_now = datetime.now(timezone.utc)

        diff = dt_now - dt_modification

        logger.debug(f"Database age: {diff.days} days (Last mod: {dt_modification})")

        return diff.days

    @staticmethod
    def fetch_releases() -> None:
        """ Fetch release data from the remote repository API

        This function performs an HTTP GET request to retrieve the latest releases,
        parses the JSON response to extract tags and names, and stores the processed
        data into the local database.

        :return: None
        :rtype: NoneType

        :raises requests.exceptions.RequestException: If the HTTP request fails.
        """

        logger.info(f"Fetching latest release from API...")
        logger.debug(f"Requesting URL: {RBXPI_REPO_API}")

        try:
            response = requests.get(RBXPI_REPO_API, timeout=10)
            response.raise_for_status()

            data = response.json()

            logger.debug(f"API response received. Processing {len(data)} potential releases.")

            releases = {}
            for index, value in enumerate(data):
                releases[index] = {
                    "tag": value.get("tag_name", "undefined"),
                    "name": value.get("name", "undefined")
                }

                releases[index]["assets"] = []
                for _, asset in enumerate(data[index]["assets"]):
                    releases[index]["assets"].append(asset.get("name", "undefined"))

            logger.info(f"Successfully fetched and parsed {len(releases)} releases.")

        except requests.exceptions.RequestException as err:
            logger.error(f"Failed to reach the API: {err}")
            exit(1)

        except Exception as err:
            logger.error(f"An unexpected error occurred during parsing: {err}")
            exit(1)

        Database.write(releases)

    @staticmethod
    def show() -> bool:
        """ Display the stored releases and database status

        This function fetches data from the database, formats it into a table-like
        string for the console, and prints a warning message if the data has not
        been updated for more than three days.

        :return: Always returns True to indicate successful execution.
        :rtype: bool
        """

        logger.info("Fetching releases from database for display...")

        releases = Database.get()
        days_since_modification = Database.get_days_since_modification()

        if not releases:
            logger.warning("No releases found in database display.")
            return False

        message = f"\nVersion{" " * 6}Name{" " * 22}Managed By\n"
        for index in releases:
            message = message + (f"{releases[index]['tag']}{" " * (13 - len(releases[index]["tag"]))}"
                                 f"{releases[index]['name']}{" " * (26 - len(releases[index]['name']))}"
                                 f"BlockGuard SF \n")

        print(message)

        if days_since_modification >= 3:
            logger.info(f"Database is outdated ({days_since_modification} days). Warning shown to user.")

            print(f"* Roblox Install Manager hasn't updated its database in a long time, please refresh it.\n"
                  f"* To maintain the reliability of rbxmanager, its database will be automatically updated {7 - days_since_modification} days after use.\n")

        return True
