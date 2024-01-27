"""Handle the --list-drivers flag."""

import pyodbc


def print_list():
    """Query pyodbc for its list of drivers, and print it.

    This can be useful to understand which drivers are available for Datum,
    without manually starting a Python interpreter (or knowledge of pyodbc).
    """
    template = '"{0}"'
    drivers_list = [template.format(d) for d in pyodbc.drivers()]
    print("Drivers available:\n", "\n".join(drivers_list), sep="")
    return
