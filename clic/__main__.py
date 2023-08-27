from register_map import sim
from argparse import ArgumentParser, Namespace


def parse_args() -> Namespace:
    """
    Parses the command line arguments.
    """
    parser = ArgumentParser(
        description="A tool for generating and testing the CLIC.",
    )
    parser.add_argument(
        "-s",
        "--simulate",
        action="store_true",
        help="Runs the simulations. Note that the environment variable $SIMULATE must be set to 1.",
        default=False,
    )
    parser.add_argument(
        "-g",
        "--generate",
        action="store_true",
        help="Generates the verilog files.",
        default=False,
    )
    ns = parser.parse_args()
    return ns


if __name__ == "__main__":
    args = parse_args()
    if args.simulate:
        # Run all simulations if the user specified the -s flag.
        sim()
