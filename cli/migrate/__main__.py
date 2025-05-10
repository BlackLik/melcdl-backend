#!/usr/bin/env python3
from internal.bootstrap.migrate import MigrateCommand


def main() -> None:
    MigrateCommand().execute()


if __name__ == "__main__":
    main()
