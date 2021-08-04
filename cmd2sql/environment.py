"""Everything related to interaction with the environment, not only env vars
but also paths and configuration.
"""
import configparser
import os


def resolve_envvar_args(args):
    """For each parameter in args (populated from docotp), replaces the value
with an env var value when prefixed with 'ENV='."""
    for key, value in args.items():
        # I'd rather str(value) than check the type, I don't know why
        if str(value).startswith("ENV="):
            args[key] = os.getenv(value[4:])


def get_config_dict(commands_arg):
    """Find and open (if present) a configuration file.
Return default configuration values if the file isn't present."""
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
                                        "cmd2sql",
                                        config_file_path)
        if os.path.isfile(config_file_path):
            return _read_config(config_file_path)
        else:
            return {"rows": 25,
                    "truncate": 25,
                    "custom_commands": {}}


def _read_config(config_file_path):
    config = {}
    config_file = configparser.ConfigParser()
    config_file.read(config_file_path)
    config["rows"] = config_file.getint("config",
                                        "rows",
                                        fallback=100)
    config["truncate"] = config_file.getint("config",
                                            "truncate",
                                            fallback=100)
    config["custom_commands"] = {}
    if "queries" in config_file:
        for name in config_file["queries"]:
            config["custom_commands"][name] = config_file["queries"][name]
    return config
