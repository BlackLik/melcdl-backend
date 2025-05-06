import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def main() -> None:
    logger.info("Hello from melcdl-backend!")


if __name__ == "__main__":
    main()
