#!/usr/bin/env python3

class Shell:
    def __init__(self):
        pass

    @staticmethod
    def input(message: str = "") -> str:
        try:
            prompt = input("> ") if not message else input(f"{message} > ")
        except KeyboardInterrupt:
            exit("\nClosing Roblox Install Manager.")

        return prompt
