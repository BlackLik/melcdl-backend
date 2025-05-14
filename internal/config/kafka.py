from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any

from internal.client.kafka.consumer import KafkaConsumer, KafkaConsumerConfig
from internal.client.kafka.producer import KafkaProducer, KafkaProducerConfig
from internal.config import get_config


@lru_cache(maxsize=1)
def get_producer_config() -> KafkaProducerConfig:
    settings = get_config()
    return KafkaProducerConfig(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    )


@lru_cache(maxsize=1)
def get_kafka_producer() -> KafkaProducer:
    return KafkaProducer(kafka_config=get_producer_config())


async def get_kafka_producer_context() -> AsyncGenerator[KafkaProducer, Any]:
    async with get_kafka_producer() as producer:
        yield producer


@lru_cache(maxsize=1)
def get_consumer_config() -> KafkaConsumerConfig:
    settings = get_config()
    return KafkaConsumerConfig(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_GROUP_ID,
    )


@lru_cache(maxsize=1)
def get_kafka_consumer() -> KafkaConsumer:
    return KafkaConsumer(kafka_config=get_consumer_config())
