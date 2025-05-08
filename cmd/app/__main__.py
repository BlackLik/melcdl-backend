import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def main() -> None:
    logger.info("Hello from melcdl-backend!")


if __name__ == "__main__":
    main()
