"""Everything related to interaction with the environment.

This includes not only env vars but also paths and configuration.
"""
import configparser
import os

# "csv_path" is set by the :csv command, it should default to None
_default_config = {"rows_to_print": 50,
                   "column_display_length": 100,
                   "null_string": "[NULL]",
                   "newline_replacement": "[NL]",
                   "tab_replacement": "[TAB]",
                   "command_timeout": 30,
                   "csv_path": None,
                   "custom_commands": {}}


def resolve_envvar_args(args):
    """Replace environment variables in each arg, when needed.

    Itearates args (populated from docotp), to replace the value with an env
    var value only when prefixed with 'ENV='.
    """
    for key, value in args.items():
        # I'd rather str(value) than check the type, I don't know why
        if str(value).startswith("ENV="):
            args[key] = os.getenv(value[4:])


def get_config_dict(commands_arg):
    """Find and open (if present) a configuration file.

    Will return the default configuration values if needed.
    """
    global _default_config
    config_file_path = os.path.expanduser(commands_arg)
    # happiest path: it is an absolute path or a relative path we can resolve
    if os.path.isfile(config_file_path):
        return _read_config(config_file_path)
    else:
        base_dir = os.getenv("XDG_CONFIG_HOME")
        # no specific XDG_CONFIG_HOME, then do fallback as outlined in
        # https://specifications.freedesktop.org/basedir-spec/latest/
        if not base_dir:
            # as seen in https://stackoverflow.com/a/4028943
            base_dir = os.path.join(os.path.expanduser("~"), ".config")
        config_file_path = os.path.join(base_dir,
                                        "datum",
                                        config_file_path)
        if os.path.isfile(config_file_path):
            return _read_config(config_file_path)
        else:
            return _default_config


def _read_config(config_file_path):
    global _default_config
    config = {}
    config_file = configparser.ConfigParser()
    config_file.read(config_file_path)
    config["rows_to_print"] = config_file.getint(
        "general",
        "rows_to_print",
        fallback=_default_config["rows_to_print"])
    config["column_display_length"] = config_file.getint(
        "general",
        "column_display_length",
        fallback=_default_config["column_display_length"])
    config["null_string"] = config_file.get(
        "general",
        "null_string",
        fallback=_default_config["null_string"])
    config["newline_replacement"] = config_file.get(
        "general",
        "newline_replacement",
        fallback=_default_config["newline_replacement"])
    config["tab_replacement"] = config_file.get(
        "general",
        "tab_replacement",
        fallback=_default_config["tab_replacement"])
    config["command_timeout"] = config_file.getint(
        "general",
        "command_timeout",
        fallback=_default_config["command_timeout"])
    config["custom_commands"] = {}
    if "queries" in config_file:
        for name in config_file["queries"]:
            config["custom_commands"][name] = config_file["queries"][name]
    # reading empty string from the config files ==> same as using the command
    # with the OFF option. So let's take care of that.
    if config["newline_replacement"] == "":
        config["newline_replacement"] = "\n"
    if config["tab_replacement"] == "":
        config["tab_replacement"] = "\t"

    # "csv_path" is set by the :csv command, and cleared after each use
    config["csv_path"] = None

    return config
