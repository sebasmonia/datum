"""
docopt definition here
"""
from docopt import docopt
from datetime import datetime
from . import cmd2sql
import logging
import sys

def main():
    args = docopt(__doc__)
    # default to root level
    if args["--debug"]:
        log_level = getattr(logging, args["--debug"].upper())
        log_file = os.path.join(os.getcwd(), "sql2cmd.debug")
        print(f"-----Writing debug information to {log_file} with",
              f"level {args['--debug']}-----\n\n")
        logging.basicConfig(filename=log_file,
                            encoding='utf-8',
                            level=log_level)
        logging.warning("-----Started running %s-----",
                        datetime.now().isoformat(sep=" ")[:19])
    else:
        logging.basicConfig(level=logging.CRITICAL)

    cmd2sql.empty()

if __name__ == "__main__":
    try:
        main()
        # on unhandled exception the exit code will be non-zero
        sys.exit(0)
    except Exception as e:
        print(e, "\n")
