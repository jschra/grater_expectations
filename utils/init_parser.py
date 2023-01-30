# -- Base Python imports
from argparse import ArgumentParser
from version import __version__


# -- Functions
def initialize_parser() -> ArgumentParser:
    """Function to initialize command line parser for the package

    Returns
    -------
    ArgumentParser
        An initialize argument parser
    """
    # -- 1. Create new parser, add (sub-)arguments
    parser = ArgumentParser(description="CLI for Grater Expectations")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    subparsers = parser.add_subparsers()

    # -- .1 Add create subparser
    create = subparsers.add_parser(
        "create", help="command to create configs and projects"
    )
    create_subparsers = create.add_subparsers(dest="create")

    # -- .2 Add config to create subparser
    create_cnf = create_subparsers.add_parser("config", help="command to create config")
    create_cnf.add_argument(
        "-p",
        "--provider",
        metavar="",
        type=str,
        required=True,
        help="Cloud provider to initialize config for",
    )

    # -- .3 Add project to create subparser
    create_prj = create_subparsers.add_parser(
        "project", help="command to create projects"
    )
    create_prj.add_argument(
        "-n", "--name", type=str, required=True, help="name of the project", metavar=""
    )
    create_prj.add_argument(
        "-nv", "--nonverbose", action="store_true", help="option for non-verbose files"
    )

    return parser
