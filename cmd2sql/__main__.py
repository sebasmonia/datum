"""Command line tool to query databases via ODBC. Friendly to Emacs SQLi mode.

Usage:
    cmd2sql (-h | --help)
    cmd2sql --conn_string=<connection_string> [--commands=<path>]
    cmd2sql (--driver=<odbc_driver> | --dsn=<dsn>)
            [--server=<server> --database=<database>]
            [--user=<username> --pass=<password> --integrated]
            [--commands=<path>]

Options:
  -h --help             Show this screen.

To provide a known connection string just use:
  --conn_string=<connection_string>

Else it will be built using the individual parameters, start with how and what
to connect to:

  --dsn=<dsn>            If using a connection defined in a DSN, specify the
                         name here.
  --driver=<driver>      The ODBC driver to use, required if not using DSN.

  --server=<server>      Server to connect to. Omit for SQLite.
  --database=<database>  Database to open. Can be omitted if it is declared in
                         a DSN.

Then for security, if needed (can be ommited for SQLite or if DSN, etc.):

  --integrated           Use Integrated Security (MSSQL). If included it takes
                         precedence over user/pass
  --user=<username>      SQL Login user
  --pass=<password>      SQL Login password

Last optional parameter:
  --commands=<path>      Path to the INI file that declares custom commands.
                         [default: $XDG_CONFIG_HOME/cmd2sql/commands.ini]

If the value for a parameter starts with ENV={name_here} then it is read from
the environment variable NAME_HERE. For example: --pass=ENV=DB_SECRET would get
the value for <password> from $DB_SECRET.
"""

from docopt import docopt
from . import cmd2sql
import sys


def main():
    args = docopt(__doc__)
    cmd2sql.print_args(args)

if __name__ == "__main__":
    try:
        main()
        # on unhandled exception the exit code will be non-zero
        sys.exit(0)
    except Exception as e:
        print("Error: ", e, "\n")
