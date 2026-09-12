"""Module entry point; stage commands are registered as they are ported."""

import argparse

from research_tools import digest, scout, verify


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command")
    verify.register(subcommands)
    scout.register(subcommands)
    digest.register(subcommands)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
