
"""Command handler for datum.

This module deals with built-in commands (:rows, :reconnect, etc.) and
processing of custom queries.
"""
from . import connect
from string import Formatter as _Formatter
import os

_config = {}

_help_text = """
--Available commands--
:help             Prints the command list.

:rows [number]    How many rows to print out of the resultset. Call with no
                  number to see the current value. Use 0 for "all rows".

:chars [number]   How many chars per column to print. Call with no number to
                  see the current value. Use 0 to not truncate.

:null [string]    String to show for "NULL" values. Call with no args
                  to see the current string. Use "OFF" (no quotes) to show
                  nothing (this makes empty string and null look the same)

:newline [string] String to replace newlines in values. Use "OFF" (no quotes)
                  to keep newlines as-is, it will most likely break the display
                  of output. Call with no arg to display the current value.

:tab [string]     String to replace tab in values. Use "OFF" (no quotes) to
                  keep tab characters. Call with no arguments to show the
                  current value.

:timeout [number] Seconds for command timeouts - how long to wait for a command
                  to finish running.

:reconnect        Force a new connection to the server, discarding the old one.

:csv [path]       Export the query output to CSV file. Call with no arguments
                  to print results again.

:script [path]    Read a script from a file. The input is processed as a custom
                  command, with support for {placeholders} and ? ODBC params.
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
    # For custom queries, or :script, this will return the formatted query.
    # Other commands return nothing, no output is printed and we get back to
    # the input prompt loop
    output_query = ""
    if command_name in _builtins:
        return _builtins[command_name](args)
    elif command_name[1:] in _config["custom_commands"]:
        return prepare_query(_config["custom_commands"][command_name[1:]])
    else:
        print("Invalid command. Use :help for a list of available commands.")

    return output_query


def help_text(args):
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
              'of query output).')
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


def csv_setup(args):
    """Built-in :csv command.

    Set the export path in the config dictionary's 'csv_path' key. This value
    is read in the main loop, to write to file rather than printing.
    """
    global _config
    if args:
        filename = ""
        try:
            filename, _ = _args_to_abspath(args)
            # Try to open the file, if there's a problem, we fail
            # RIGHT NOW and inform the user why.
            open(filename, 'a').close()
            # if we got here, then the path is valid
            _config["csv_path"] = filename
        except Exception as err:
            print('ERROR opening file"', filename, '". Invalid path?',
                  sep="")
            return
        print('CSV target "', _config["csv_path"], '"', sep="")
    else:
        # disable export if no parameter is provided
        _config["csv_path"] = None
        print("Disabled CSV writing")


def read_script(args):
    """Built-in :script command.

    Read the content of a file and return it as custom query text.
    """
    if args:
        filename = ""
        try:
            filename, exists = _args_to_abspath(args)
            if not exists:
                print('File "', filename, '" does not exist', sep="")
                return
            with open(filename, 'r', encoding='utf-8') as script:
                # Load all content before saying the file is loaded, and also
                # remove all leading and trailing whitespace
                text = script.read().strip()
                print('Loaded script file "', filename, '"', sep="")
                return prepare_query(text)
        except Exception as err:
            print('ERROR reading file"', filename, '"', sep="")
            return
    else:
        print('No input path provided', sep="")
        return


def reconnect(args):
    """Built-in :reconnect command."""
    # Since the timeout command modified the config dict, and the timeout in
    # the function below is picked up from the same place...
    connect.get_connection(force_new=True)
    # if get_connection throws, this message won't print
    print("Opened new connection.")
    # Making pyright happy, no one cares about the return value of this
    return


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
    formatted_query = template.format(**kwargs)
    print("Command query:\n", formatted_query)
    return formatted_query


def _args_to_abspath(args):
    """Join args and return it as an absolute path.
    Also confirm if the path exists.

    Helper for :csv and :script
    """
    filename = " ".join(args)
    filename = os.path.abspath(filename)
    return (filename, os.path.exists(filename))


_builtins = {":help": help_text,
             ":rows": rows,
             ":chars": chars,
             ":null": null,
             ":newline": newline,
             ":tab": tab,
             ":timeout": timeout,
             ":csv": csv_setup,
             ":script": read_script,
             ":reconnect": reconnect}
