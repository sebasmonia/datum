"""Contains all the setup for new connections to the database.
"""
import pyodbc
import struct

# module "local" variables
_connection = None
_conn_string = None
_driver = None
_dsn = None
_server = None
_database = None
_user = None
_pass = None
_integrated = False
_timeout = 30

# The first newline here is useful for spacing later
_header_message = """
Special commands are prefixed with ":". For example, use ":exit" or ":quit" to
finish your session. Use ":help" to list available commands.
Everything else is sent directly to the server using ODBC when you type "GO" in
a new line or ";;" at the end of a query.
"""


def initialize_module(docopt_args, config):
    global _conn_string, _driver, _dsn, _server, _database, _user, _pass
    global _integrated, _timeout
    _conn_string = docopt_args["--conn_string"]
    if docopt_args["--conn_string"]:
        # We will use the connection string as-is
        # but attempt to extract server/dsn and db name for the prompt
        components = _conn_string.split(";")
        for piece in components:
            if 'dsn' in piece:
                _, value = piece.split("=")
                _dsn = value
            if 'server' in piece:
                _, value = piece.split("=")
                _server = value
            if 'database' in piece:
                _, value = piece.split("=")
                _database = value
        return

    _driver = docopt_args["--driver"]
    _dsn = docopt_args["--dsn"]
    _server = docopt_args["--server"]
    _database = docopt_args["--database"]
    _user = docopt_args["--user"]
    _pass = docopt_args["--pass"]
    _integrated = docopt_args["--integrated"]
    _timeout = config["command_timeout"]
    _build_connection_string()


def show_connection_banner_and_get_prompt_header():
    global _server, _database, _dsn, _header_message
    # If the server name isn't explicit, then use the DSN name. Even then,
    # something like SQLite might now have server nor DSN, so show "-"
    print_server = _server or _dsn or "-"
    print('Connected to server', print_server, end=" ")
    if _database:
        print('database', _database)
    print(_header_message)
    return print_server + ("@" + _database if _database else "")


def get_connection():
    global _conn_string, _connection, _timeout

    if _connection:
        return _connection

    _connection = pyodbc.connect(_conn_string, autocommit=True)
    _connection.add_output_converter(-155, _handle_datetimeoffset)
    _connection.timeout = _timeout
    return _connection


def _build_connection_string():
    global _conn_string, _driver, _dsn, _server, _database, _user, _pass
    global _integrated
    _conn_string = ""
    if _dsn:
        _conn_string += f"DSN={_dsn};"
    if _driver:
        _conn_string += f"Driver={_driver};"
    if _server:
        _conn_string += f"Server={_server};"
    if _database:
        _conn_string += f"Database={_database};"
    if _integrated:
        _conn_string += f"Trusted_Connection=Yes;"
    if _user:
        _conn_string += f"Uid={_user};"
    if _pass:
        _conn_string += f"Pwd={_pass};"


# source:
# https://github.com/mkleehammer/pyodbc/wiki/Using-an-Output-Converter-function
def _handle_datetimeoffset(dto_value):
    # see also:
    # https://github.com/mkleehammer/pyodbc/issues/134#issuecomment-281739794
    tup = struct.unpack("<6hI2h", dto_value)
    tweaked = [tup[i] // 100 if i == 6 else tup[i] for i in range(len(tup))]
    t = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}.{:07d} {:+03d}:{:02d}"
    return t.format(*tweaked)
