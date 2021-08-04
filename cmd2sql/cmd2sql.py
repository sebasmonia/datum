"REPL loop module."

from . import connect
from . import environment

# builtin_commands = {":help": command_help,
#                     ":truncate": command_truncate,
#                     ":rows": command_rows,
#                     ":file": command_file,
#                     ":use": command_use,
#                     ":timeout": command_timeout}
custom_commands = {}


def initialize(args):
    global custom_commands
    environment.resolve_envvar_args(args)
    config = environment.get_config_dict(args["--config"])
    custom_commands = config["custom_commands"]
    connect.initialize(args)
    # connect.get_connection()
