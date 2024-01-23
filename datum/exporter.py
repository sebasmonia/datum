"""Datum's CSV exporter."""
import csv
from pyodbc import ProgrammingError

_config = {}


def initialize_module(config):
    """Initialize this module with a reference to the global config."""
    global _config
    _config = config


def export_cursor_results(a_cursor):
    """Export to CSV the results of a cursor.

    Most queries have one resultset, but if there's more than one, add a suffix
    to the path.
    """
    global _config
    # Before trying anything, clear the value from the config dict.
    # Even if there's an error, we should go back to printing results.
    path = _config["csv_path"]
    _config["csv_path"] = None
    try:
        export_resultset(path, a_cursor)
    except ProgrammingError as e:
        if "Previous SQL was not a query." in str(e):
            pass
        else:
            raise e
    suffix = 1
    while a_cursor.nextset():
        try:
            new_path = "{0}_{1}".format(path, suffix)
            suffix += 1
            # Newline to separate each file output
            print()
            export_resultset(new_path, a_cursor)
        except ProgrammingError as e:
            if "Previous SQL was not a query." in str(e):
                continue
            else:
                raise e

def export_resultset(path, cursor):
    """Export the results of cursor (the "current" resultset).

    This function will attempt to keep the user updated as the export happens.
    """
    batch_size = 10000
    print('Writing to file, one ! per', batch_size, 'rows:')
    with open(path, 'w', encoding='utf-8') as outputfile:
        writer = csv.writer(outputfile)
        # column headers are written even if no rows are returned
        writer.writerow([column[0] for column in cursor.description])
        rows = cursor.fetchmany(batch_size)
        while rows:
            writer.writerows(rows)
            print("!", end="", flush=True)
            rows = cursor.fetchmany(batch_size)
