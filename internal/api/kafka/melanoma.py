from aiokafka import ConsumerRecord

from internal.api.kafka import KafkaActions
from internal.utils import log

actions = KafkaActions()
logger = log.get_logger()


@actions.read("melanoma-detection")
async def read_melanoma_detection(msg: ConsumerRecord) -> None:
    logger.info("Received message: %s", msg.value)
