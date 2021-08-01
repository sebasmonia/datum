from . import connect


def print_args(args):
    print(args)
    connect.initialize(args)
    connect.get_connection()
