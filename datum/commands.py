"""Command handler for datum.

This module deals with built-in commands (:rows, :reconnect, etc.) and
processing of custom queries.
"""
from . import connect
from string import Formatter as _Formatter

_config = {}

_help_text = """
--Available commands--
:help             Prints the command list.

:rows [number]    How many rows to print out of the resultset. Call with no
                  number to see the current value. Use 0 for "all rows".

:chars [number]   How many chars per column to print. Call with no number to
                  see the current value. Use 0 to not truncate.

:null [string]    String to show for "NULL" in the database. Call with no args
                  to see the current string. Use "OFF" (no quotes) to show
                  nothing. Note that this makes empty string and null hard to
                  differentiate.

:newline [string] String to replace newlines in values. Use "OFF" (no quotes)
                  to keep newlines as-is, it will most likely break the display
                  of output. Call with no arg to display the current value.

:tab [string]     String to replace tab in values. Use "OFF" (no quotes) to
                  keep tab characters. Call with no arguments to show the
                  current value.

:timeout [number] Seconds for command timeouts - how long to wait for a command
                  to finish running.

:reconnect        Force a new connection to the server, discarding the old one.
"""


def initialize_module(config):
    """Initialize this module with a reference to the global config."""
    global _config, _custom_commands
    _config = config


def handle(user_input):
    """As it says on the tin, handle a command."""
    # built ins dictionary is defined at the bottom of the file
    global _builtins
    # we got here with confirmation that this is a command, so:
    command_name, *args = user_input.strip().split(" ")
    # For custom queries, this will return the formatted query. Other commands
    # return empty, no output is printed and we get back to the prompt
    output_query = ""
    if command_name in _builtins:
        _builtins[command_name](args)
    elif command_name[1:] in _config["custom_commands"]:
        output_query = prepare_query(
            _config["custom_commands"][command_name[1:]])
        print("Command query:\n", output_query)
    else:
        print("Invalid command. Use :help for a list of available commands.")

    return output_query


def help(args):
    """Built-in :help command."""
    global _help_text, _config
    print(_help_text)
    if _config["custom_commands"]:
        print('Commands declared in the "queries" section of the ',
              'configuration file:')
        line = ""
        for key in _config["custom_commands"].keys():
            # This will break if people start defining _really long_
            # query names...
            if len(line) + len(key) > 79:
                print(line[:-1])  # don't print the last space...
                line = key + ", "
            else:
                line += key + ", "
        print(line[:-2])  # don't print the last comma and space


def rows(args):
    """Built-in :rows command."""
    global _config

    if args:
        try:
            new_value = int(args[0])
            if new_value < 0:
                raise ValueError("Why are you trying to break me...")
            _config["rows_to_print"] = new_value
        except ValueError:
            pass
    display_value = ("ALL" if not _config["rows_to_print"] else
                     _config["rows_to_print"])
    print('Printing', display_value, 'rows of each resulset.')


def chars(args):
    """Built-in :chars command."""
    global _config

    if args:
        try:
            new_value = int(args[0])
            if new_value < 0:
                raise ValueError("Why are you trying to break me...")
            _config["column_display_length"] = new_value
        except ValueError:
            pass
    if not _config["column_display_length"]:
        print('Printing ALL characters of each column.')
    else:
        print('Printing a maximum of', _config["column_display_length"],
              'characters of each column.')


def null(args):
    """Built-in :null command."""
    global _config

    if args and args[0] == "OFF":
        _config["null_string"] = ""
    elif args and args[0] != "OFF":
        _config["null_string"] = args[0]

    print('Using the string "', _config["null_string"],
          '" to print NULL values.', sep='')


def newline(args):
    """Built-in :newline command."""
    global _config

    if args and args[0] == "OFF":
        _config["newline_replacement"] = "\n"
    elif args and args[0] != "OFF":
        _config["newline_replacement"] = args[0]

    if _config["newline_replacement"] == "\n":
        print('Printing newlines with no conversion (might break the display',
              'of query output.')
    else:
        print('Using the string "', _config["newline_replacement"],
              '" to print literal new lines in values.', sep='')


def tab(args):
    """Built-in :tab command."""
    global _config

    if args and args[0] == "OFF":
        _config["tab_replacement"] = "\t"
    elif args and args[0] != "OFF":
        _config["tab_replacement"] = args[0]

    if _config["tab_replacement"] == "\t":
        print('Printing tabs with no conversion (might break the display of',
              'query output).')
    else:
        print('Using the string "', _config["tab_replacement"],
              '" to print literal tabs in values.', sep='')


def timeout(args):
    """Built-in :timeout command."""
    global _config
    # By the time we are in a position to handle this command, there's an open
    # connection we have been using
    connection = connect.get_connection()

    if args:
        try:
            new_value = int(args[0])
            if new_value < 0:
                raise ValueError("Why are you trying to break me...")
            connection.timeout = new_value
            _config["command_timeout"] = new_value
        except ValueError:
            pass
    print("Command timeout set to", connection.timeout, "seconds.")


def reconnect(args):
    """Built-in :reconnect command."""
    # Since the timeout command modified the config dict, and the timeout in
    # the function below is picked up from the same place...
    connect.get_connection(force_new=True)
    # if get_connection throws, this message won't print
    print("Opened new connection.")
    # Making pyright happy, no one cares about the return value of this
    return args


def prepare_query(template):
    """Replace the {} placeholders in a query template with user input."""
    f = _Formatter()
    # A set built out of the replacement keys present after the Formatter
    # parses the input
    kwargs_keys = {item[1] for item in f.parse(template) if item[1]}
    kwargs = {}
    for key in kwargs_keys:
        value = input(f"{key}>")
        kwargs[key] = value
    if kwargs:
        print()  # add an empty line if we read parameters
    # This could throw an error under a number of situations, but we'll let it
    # bubble so it is handled (and printed) on datum.query_loop
    return template.format(**kwargs)


_builtins = {":help": help,
             ":rows": rows,
             ":chars": chars,
             ":null": null,
             ":newline": newline,
             ":tab": tab,
             ":timeout": timeout,
             ":reconnect": reconnect}
