"REPL loop module."

from . import connect
from . import environment
from . import printer

# builtin_commands = {":help": command_help,
#                     ":truncate": command_truncate,
#                     ":rows": command_rows,
#                     ":file": command_file,
#                     ":use": command_use,
#                     ":timeout": command_timeout}
config = None


def initialize(args):
    global config
    environment.resolve_envvar_args(args)
    config = environment.get_config_dict(args["--config"])
    connect.initialize(args)
    printer.initialize(config)
    # we don't _need_ to connect now, but it is a good place to blow up
    # if the parameters we have aren't good
    connect.get_connection()


def query_loop():
    prompt_header = connect.show_connection_banner_and_get_prompt_header()
    print(prompt_header)
    query = prompt_for_query_or_command()
    row_count = 0
    while query not in (":exit", ":quit"):
        try:
            if query.startswith(":"):
                print("do command here")
            if query:
                cursor = connect.get_connection().cursor()
                params = prompt_parameters(query)
                cursor.execute(query, params)
                printer.print_cursor_results(cursor)
                row_count = cursor.rowcount
            print("\nRows affected:", row_count, flush=True)
        except Exception as err:
            print("---ERROR---\n", err, "\n---ERROR---", flush=True)
        print(flush=True)  # blank line
        print(prompt_header)
        query = prompt_for_query_or_command()


def prompt_for_query_or_command():
    lines = []
    while True:
        lines.append(input(">"))
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
    # My thinking here is that  we should count "?" next to a space and
    # next to an operator. Ex: " ? ", ",?", "=?" Not sure if that is safe
    # enough, but it seems better than plainly counting "?" like sqlcmdline
    # used to do, so, it is an improvement.
    param_count = query.count(" ?")
    param_count += query.count(",?")
    param_count += query.count("=?")
    params = []
    for param_num in range(1, param_count + 1):
        params.append(input(f"{param_num}>"))
    return params
