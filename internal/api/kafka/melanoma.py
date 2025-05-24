from aiokafka import ConsumerRecord

from internal import config
from internal.api.kafka import KafkaActions
from internal.entities import schemas
from internal.utils import log

actions = KafkaActions()
logger = log.get_logger()


@actions.read(config.get_config().KAFKA_TOPIC_MELANOMA_ML)
async def read_melanoma_detection(msg: ConsumerRecord) -> None:
    message = schemas.ml.KafkaInputMessageSchema.model_validate_json(msg.value)
    logger.info("Received message: %s", message)
