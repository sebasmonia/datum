"""REPL loop module."""

from . import connect
from . import environment
from . import printer
from . import exporter
from . import commands

# The configuration read using environment.get_config_dict and referenced in
# this variable is, in fact, shared by all the modules. This allows the
# commands to change config on the fly easily. There some risk of introducing
# bugs, so let's keep it in mind in all the code...
config = None


def initialize(args):
    """Instantiate the global config, and init the sub-modules with it."""
    global config
    environment.resolve_envvar_args(args)
    config = environment.get_config_dict(args["--config"])
    connect.initialize_module(args, config)
    printer.initialize_module(config)
    exporter.initialize_module(config)
    commands.initialize_module(config)
    # we don't _need_ to connect now, but it is a good place to blow up
    # if the parameters we have aren't good
    connect.get_connection()


def query_loop():
    """Query loop for Datum.

    This function orchestrates the display of the prompt, running queries or
    commands, and printing the results, if any.
    """
    global config
    prompt_header = connect.show_connection_banner_and_get_prompt_header()
    print(prompt_header)
    query = prompt_for_query_or_command()
    row_count = 0
    while query not in (":exit", ":quit"):
        try:
            if query.startswith(":"):
                # a command might return a formatted query, or nothing
                query = commands.handle(query)
            # see the comment in the if block above: this might be the user's
            # input if it wasn't a command, OR empty if it was handled and
            # there's nothing else to do, OR a formatted query
            if query:
                cursor = connect.get_connection().cursor()
                params = prompt_parameters(query)
                cursor.execute(query, params)
                row_count = cursor.rowcount
                if config["csv_path"]:
                    exporter.export_cursor_results(cursor)
                else:
                    # the default operation
                    printer.print_cursor_results(cursor)
                print("\nRows affected:", row_count)
        except Exception as err:
            print("---ERROR---\n", err, "\n---ERROR---", flush=True)
        # Print newline + prompt, then flush. Attemp to fix issue #8
        print("\n", prompt_header, sep="", flush=True)
        query = prompt_for_query_or_command()


def prompt_for_query_or_command():
    """Read the user's input, waiting for "query terminators" or commands."""
    global config
    lines = []
    # New in version 0.6: if output to file was request, add a "csv" to the
    # prompt string
    prompt = "csv>" if config["csv_path"] else ">"
    while True:
        lines.append(input(prompt))
        last = lines[-1]
        if last.strip()[-2:] == ";;":
            # Exclude extra ";"
            return '\n'.join(lines)[:-1]
        if last.strip().upper().startswith('GO'):
            # Exclude GO
            return '\n'.join(lines[:-1])
        if last.startswith(":"):
            # For commands, ignore all prior input
            return last


def prompt_parameters(query):
    """Analyze the query text and read as many parameters as needed.

    The logic to detemine how many parameters to read is somewhat fragile.
    """
    # My thinking here is that  we should count "?" next to a space and
    # next to an operator. Ex: " ? ", ",?", "=?" Not sure if that is safe
    # enough, but it seems better than plainly counting "?" like sqlcmdline
    # used to do, so, it is an improvement.
    param_count = query.count(" ?")
    param_count += query.count(",?")
    param_count += query.count("=?")
    params = []
    if param_count > 0:
        # Add an empty line before asking for parameters, if any. This is a
        # a very pragmatic fix to https://github.com/sebasmonia/datum/issues/4
        print()
    for param_num in range(1, param_count + 1):
        params.append(input(f"{param_num}>"))
    return params
