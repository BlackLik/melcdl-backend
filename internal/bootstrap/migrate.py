import argparse
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from internal.bootstrap.abc import AbstractCommand
from internal.utils import log

logger = log.get_logger()


class MigrateCommand(AbstractCommand):
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

        args = self.parse_args()
        cfg = self.get_alembic_config()
        action = args.action or "upgrade"

        commands = {
            "upgrade": lambda: command.upgrade(cfg, args.revision),
            "downgrade": lambda: command.downgrade(cfg, args.revision),
            "revision": lambda: command.revision(cfg, message=args.message, autogenerate=True),
        }

        if action not in commands:
            msg = f"Unknown command: {action}"
            raise ValueError(msg)

        logger.info("Running alembic %s", action)
        commands[action]()

    def get_alembic_config(self) -> Config:
        """
        Locate and load the Alembic configuration file.
        """
        config_file = Path(__name__).parent / "alembic.ini"
        if not config_file.is_file():
            logger.error("Alembic config not found: %s", config_file)
            raise FileNotFoundError

        return Config(str(config_file))

    def parse_args(self) -> argparse.Namespace:
        """
        Parse CLI arguments for migration commands.
        """
        parser = argparse.ArgumentParser(
            prog="python -m cli.migration", description="Manage Alembic database migrations."
        )
        subparsers = parser.add_subparsers(dest="action")

        # upgrade command
        parser_upgrade = subparsers.add_parser(
            "upgrade", help="Apply migrations up to the specified revision (default: head)."
        )
        parser_upgrade.add_argument("revision", nargs="?", default="head", help="Target revision identifier.")

        # downgrade command
        parser_downgrade = subparsers.add_parser(
            "downgrade", help="Revert migrations down to the specified revision (default: -1)."
        )
        parser_downgrade.add_argument("revision", nargs="?", default="-1", help="Target revision identifier.")

        # revision command
        parser_revision = subparsers.add_parser("revision", help="Create a new migration script with autogenerate.")
        parser_revision.add_argument("-m", "--message", required=True, help="Message for the new revision.")

        return parser.parse_args()
