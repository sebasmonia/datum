"""Datum's query output printer.
"""

from pyodbc import ProgrammingError

_rows_to_print = None
_col_display_length = None


def initialize(config):
    global _rows_to_print, _col_display_length
    _rows_to_print = config["rows"]
    _col_display_length = config["truncate"]


def print_cursor(a_cursor):
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
    print(a_cursor)
    global _rows_to_print
    if _rows_to_print:
        odbc_rows = a_cursor.fetchmany(_rows_to_print)
    else:
        odbc_rows = a_cursor.fetchall()

    rowcount = a_cursor.rowcount
    if not odbc_rows:
        return  # no rows returned!
    column_names = [text_formatter(column[0]) for column in cursor.description]
    format_str, print_ready = format_rows(column_names, odbc_rows)
    print()  # blank line
    # Issue #3, printing too slow. Trade off memory for speed when printing
    # a resultset
    print("\n".join(format_str.format(*row) for row in print_ready),
          flush=True)
    # Try to determine if all rows returned were printed
    # MS SQL Server doesn't report the total rows SELECTed,
    # but for example MySql does.
    printed_rows = len(odbc_rows)
    if printed_rows < max_rows_print or max_rows_print == 0:
        # We printed everything via :rows 0, or less than the max to print
        # in which case we can deduct there were no more rows
        rowcount = printed_rows
    if rowcount == -1:
        # Curse you, MS SQL Driver!
        rowcount = "(unknown)"
    # We tried our best! report the numbers
    print(f"\nRows printed: {printed_rows}/{rowcount}\n",
          flush=True)


def text_formatter(value):
    global _truncate
    value = str(value)
    value = str.translate(value, chars_to_cleanup)
    if _truncate and len(value) > _truncate:
        value = value[:max_column_width-5] + "[...]"
    return value

def format_rows(column_names, raw_rows):
    # lenghts will match columns by position
    column_widths = defaultdict(lambda: 0)
    formatted = []
    for row in raw_rows:
        new_row = []
        for index, value in enumerate(row):
            new_value = "#unknown#"
            if value is None:
                new_len = 6
                new_value = "[NULL]"
            if isinstance(value, bool):
                new_len = 6
                new_value = value
            elif isinstance(value, datetime):
                new_len = 26
                new_value = value.isoformat()
            # order matters, datetime matches date :)
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
    sign, digits, _ = decimal_number.as_tuple()
    # digits + separator + sign (where sign is either 0 or 1 for negatives)
    return len(digits) + 1 + sign
