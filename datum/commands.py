"""Command handler for datum.
This module deals with built-ins and processing of custom queries.
"""
_builtin_commands = {":help": command_help,
                     ":rows": command_rows,
                     ":chars": command_chars,
                     ":null": command_chars,
                     ":newline": command_chars,
                     ":tab": command_chars,
                     ":use": command_use,
                     ":file": command_file,
                     ":timeout": command_timeout}

_config = {}


def initialize_module(config):
    global _config, _custom_commands
    _config = config
