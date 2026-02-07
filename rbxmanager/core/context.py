#!/usr/bin/env python3

import logging
logger = logging.getLogger("main")

import argparse


class Context:
    def __init__(self, app_version: str, operating_system: str, args: argparse.Namespace) -> None:
        self.version = app_version
        self.os = operating_system
        self.args = args

        logger.debug(f"Context initialized (version={self.version}, os={self.os}, args={self.args})")
