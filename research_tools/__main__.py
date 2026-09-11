"""Module entry point; stage commands are registered as they are ported."""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command")
    # Stage modules will register their argument parsers here.
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
