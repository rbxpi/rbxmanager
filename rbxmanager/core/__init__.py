#!/usr/bin/env python3

import argparse
import datetime
import calendar

from common.miscellaneous import clear_screen
from .context import Context
from .services.install import Install
from .services.update import Update


class RbxManager:
    def __init__(self, app_version: str, operating_system: str, args: argparse.Namespace) -> None:
        self.context = Context(app_version, operating_system, args)
        self.action = ""

        clear_screen()

        self.header()
        self.ask_actions()

    def header(self):
        ftime = datetime.datetime.now()
        month = calendar.month_abbr[ftime.month]

        print(f"RbxPI Install Manager {self.context.version} "
              f"({month} {ftime.day} {ftime.year}, {ftime.hour}:{ftime.minute}:{ftime.second}) "
              f"{"[DEBUG] " if self.context.args.debug else ""}on {self.context.os}\n")

    def ask_actions(self):
        self.action = input("What do you want to do?\nInstall RbxPI on a new project or update an existing version? "
                       "[install/update] : ")

        if self.action in ["install", "i"]:
            Install()
        elif self.action in ["update", "u"]:
            Update()
