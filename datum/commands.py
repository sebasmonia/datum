"""Command handler for datum.
This module deals with built-ins and processing of custom queries.
"""
from . import connect

_config = {}

_help_text = """
--Available commands--
:help prints the command list
:rows [number]    How many rows to print out of the resultset. Call with no
                  number to see the current value. Use 0 for "all rows".

:chars [number]   How many chars per column to print. Call with no number to
                  see the current value. Use 0 to not truncate.

:null [string]    String to show for "NULL" in the database. Call with no args
                  to see the current string.

:newline [string] String to replace newlines in values. Use "\n" (no quotes) to
                  keep newlines as-is, it will most likely break the output
                  table. Call with no argument to display the current value.

:tab [string]     String to replace tab in values. Use "\t" (no quotes) to keep
                  tab characters. Call with no args to show the current value.

:timeout [number] Seconds for command timeouts - how long to wait for a command
                  to finish running.
"""
# :file [-enc] path{sep}Opens a file and runs the script. No checking'
# /parsing of the file will take place. Use -enc to change the '
# encoding\nused to read the file. Examples: -utf8, -cp1250\n'
# :dbs database_name{sep}List all databases, or databases "like '
# database_name".\n'
# :use database_name{sep}changes the connection to "database_name".\n'
# :timeout [seconds]{sep}sets the command timeout. '
# Default: 30 seconds.')
# """


def initialize_module(config):
    global _config, _custom_commands
    _config = config


def handle(user_input):
    # built ins dictionary is defined at the bottom of the file
    global _builtins
    # we got here with confirmation that this is a command, so:
    command_name, *args = user_input.split(" ")
    # For custom queries, this will return the formatted query. Other commands
    # return empty, no output is printed and we get back to the prompt
    output_query = ""
    if command_name in _builtins:
        _builtins[command_name](args)
    else:
        # custom queries
        pass
    return output_query


def help(args):
    global _help_text
    print(_help_text)
    print("show other commands here")
    # Return value is not used, but pyright won't complain about args being
    # unusused :)
    return args


def rows(args):
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
    global _config

    if args:
        _config["null_string"] = args[0]

    print('Using the string "', _config["null_string"],
          '" to print NULL values.', sep='')


def newline(args):
    global _config

    if args:
        _config["newline_replacement"] = args[0]

    print('Using the string "', _config["newline_replacement"],
          '" to print literal \\n (new lines) in values.', sep='')


def tab(args):
    global _config

    if args:
        _config["tab_replacement"] = args[0]

    print('Using the string "', _config["tab_replacement"],
          '" to print literal \\t (tabs) in values.', sep='')


def timeout(args):
    # By the time we are in a position to handle this command, there's an open
    # connection we have been using
    connection = connect.get_connection()

    if args:
        try:
            new_value = int(args[0])
            if new_value < 0:
                raise ValueError("Why are you trying to break me...")
            connection.timeout = new_value
        except ValueError:
            pass
    print("Command timeout set to", connection.timeout, "seconds.")


_builtins = {":help": help,
             ":rows": rows,
             ":chars": chars,
             ":null": null,
             ":newline": newline,
             ":tab": tab,
             # these two are on probation...
             # ":use": command_use,
             # ":file": command_file,
             ":timeout": timeout}
