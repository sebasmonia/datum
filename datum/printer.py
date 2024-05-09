"""Datum's query output printer."""
from collections import defaultdict
from datetime import datetime, date, time
from pyodbc import ProgrammingError
import decimal
import math
import operator as op

_config = {}


def initialize_module(config):
    """Initialize this module with a reference to the global config."""
    global _config
    # As of this writing the printer needs _all_ the config parameters to work
    # so let's just keep the whole dict referenced
    _config = config


def print_cursor_results(a_cursor):
    """Print the current cursor resultset and (try to) move to the next one.

    Most queries have a single resulset, but stored procs for example use the
    extra logic.
    Note that the actual printing of output happens in print_resultset().
    """
    try:
        print_resultset(a_cursor)
    except ProgrammingError as e:
        if "Previous SQL was not a query." in str(e):
            pass
        else:
            raise e
    while a_cursor.nextset():
        try:
            print_resultset(a_cursor)
        except ProgrammingError as e:
            if "Previous SQL was not a query." in str(e):
                continue
            else:
                raise e


def print_resultset(a_cursor):
    """Print the results of cursor (the "current" resultset).

    This function is a performance disgrace waiting to happen. It might (when
    :rows 0) fetch ALL THE ROWS of the cursor, and then there is always a full
    iteration to determine the printing width.
    I would argue though, that no one would use datum to print millions of
    rows at a time.
    """
    global _config
    rows_to_print = _config["rows_to_print"]
    if rows_to_print:
        odbc_rows = a_cursor.fetchmany(rows_to_print)
    else:
        odbc_rows = a_cursor.fetchall()

    rowcount = a_cursor.rowcount
    # TODO: Revisit printing column headers only
    # Why is this commented out? well, turns out it can be useful to print the
    # column names even if there's no rows, and the cost of doing so is very
    # low. So, as an experiment, let's see how this behaves for a while...
    # if not odbc_rows:
    #     return  # no rows returned!
    column_names = [text_formatter(column[0]) for column in
                    a_cursor.description]
    format_str, print_ready = format_rows(column_names, odbc_rows)
    print()  # blank line
    print("\n".join(format_str.format(*row) for row in print_ready))
    # Try to determine if all rows returned were printed
    # MS SQL Server doesn't report the total rows SELECTed,
    # but for example MySql does.
    printed_rows = len(odbc_rows)
    if printed_rows < rows_to_print or rows_to_print == 0:
        # We printed everything via :rows 0, or less than the max to print
        # in which case we can deduct there were no more rows
        rowcount = printed_rows
    if rowcount == -1:
        # Curse you, MS SQL Driver!
        rowcount = "(unknown)"
    # We tried our best! report the numbers
    print("\nRows printed: ", printed_rows, "/", rowcount, sep="")


def text_formatter(value):
    """Format text for printing.

    This function will replace newlines and tabs with the currently configured
    values, and do char width truncation if needed.
    """
    global _config
    chars_to_replace = str.maketrans({"\n": _config["newline_replacement"],
                                      # TODO: experimental, completely remove
                                      # \r, since \n is treated as newline
                                      # already
                                      "\r": "",
                                      "\t": _config["tab_replacement"]})
    col_width = _config["column_display_length"]
    value = str(value)
    value = str.translate(value, chars_to_replace)
    if col_width and len(value) > col_width:
        value = value[:col_width-5] + "[...]"
    return value


def format_rows(column_names, raw_rows):
    """Go over all the rows in the results and format them for printing.

    This depends on both the data type and the configuration of this session.
    """
    global _config
    null_string = _config["null_string"]
    # lengths will match columns by position
    column_widths = defaultdict(lambda: 0)
    formatted = []
    for row in raw_rows:
        new_row = []
        new_len = 0
        for index, value in enumerate(row):
            # This will be printed whenever there isn't a proper conversion for
            # a value. It used to print 'unknown', which made me think I was
            # dealing with a real SQL value when it happened. So let's make
            # SUPER EXPLICIT that the printer tripped.
            # Also, setup a proper length so the output still looks nice :)
            new_value = "#DatumPrinterBroke#"
            new_len = 19
            if value is None:
                new_len = 6
                new_value = null_string
            if isinstance(value, bool):
                new_len = 6
                new_value = value
            elif isinstance(value, time):
                new_value = value.isoformat()
                new_len = len(new_value)
            elif isinstance(value, datetime):
                new_value = value.isoformat()
                new_len = len(new_value)
            elif isinstance(value, date):
                new_len = 10
                new_value = value.isoformat()
            elif isinstance(value, int):
                new_len = int_len(value)
                new_value = value
            elif isinstance(value, (float, decimal.Decimal)):
                new_len = decimal_len(decimal.Decimal(value))
                new_value = value
            elif isinstance(value, str):
                new_value = text_formatter(value)
                new_len = len(new_value)
            elif isinstance(value, bytes):
                # Bytes are converted to string, and it is important to
                # truncate them too. Imagine printing a whole file as binary!
                # The 0x prefix was inspired by SSMS :)
                new_value = text_formatter('0x' + value.hex())
                new_len = len(new_value)
            if new_len > column_widths[index]:
                column_widths[index] = new_len
            new_row.append(new_value)
        formatted.append(tuple(new_row))

    for index, col_name in enumerate(column_names):
        column_widths[index] = max((column_widths[index], len(col_name)))

    format_str = "|".join(["{{{ndx}:{len}}}".format(ndx=ndx, len=len)
                           for ndx, len in column_widths.items()])
    formatted.insert(0, column_names)
    # IIRC now dicts are ordered but just in case/for other implementations
    formatted.insert(1, ["-"*width for index, width in
                         sorted(column_widths.items(),
                                key=op.itemgetter(0))])
    return format_str, formatted


def int_len(number):
    """Calculate the length, in characters, of an integer."""
    # Source:
    # http://stackoverflow.com/questions/2189800/length-of-an-integer-in-python
    if number > 0:
        digits = int(math.log10(number))+1
    elif number == 0:
        digits = 1
    else:
        digits = int(math.log10(-number))+2  # +1 if you don't count the '-'
    return digits


def decimal_len(decimal_number):
    """Calculate the length, in characters, of a number with decimals."""
    sign, digits, _ = decimal_number.as_tuple()
    # digits + separator + sign (where sign is either 0 or 1 for negatives)
    return len(digits) + 1 + sign
