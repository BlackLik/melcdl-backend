from collections.abc import Awaitable, Callable
from typing import Any, Self

import aiokafka
from pydantic import BaseModel

from internal.utils import errors, log

logger = log.get_logger()


class KafkaActions:
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix or ""
        self.handlers: list[tuple[str, Callable[[aiokafka.ConsumerRecord], Awaitable[None]]]] = []
        self.dict_handlers: dict[str, Callable[[aiokafka.ConsumerRecord], Awaitable[None]]] = {}

    def read(self, topic_prefix: str) -> Callable[[Callable[[aiokafka.ConsumerRecord], Awaitable[None]]], None]:
        def wrapper(
            func: Callable[[aiokafka.ConsumerRecord], Awaitable[Any]],
        ) -> None:
            self.handlers.append((self.prefix + topic_prefix, func))
            self.dict_handlers.clear()

        return wrapper

    def include_action(self, kafka_action: Self) -> None:
        self.handlers.extend((self.prefix + name, func) for name, func in kafka_action.handlers)

    def get_handler(self, topic: str) -> Callable[[aiokafka.ConsumerRecord], Awaitable[None]]:
        handler = self.get_handlers().get(topic, None)
        if not handler:
            detail = f"Not found handler to topic: {topic!s}"
            raise errors.NotFoundError(detail=detail)

        return handler

    def get_handlers(self) -> dict[str, Callable[[aiokafka.ConsumerRecord], Awaitable[Any]]]:
        if not self.dict_handlers:
            self.dict_handlers = dict(self.handlers)
        return self.dict_handlers

    def get_topics(self) -> list[str]:
        logger.info("%s", list(self.get_handlers().keys()))
        return list(self.get_handlers().keys())


class KafkaConsumerConfig(BaseModel):
    loop: Any | None = None
    bootstrap_servers: str = "localhost"
    client_id: str = "aiokafka-" + aiokafka.__version__
    group_id: Any | None = None
    group_instance_id: Any | None = None
    key_deserializer: Any | None = None
    value_deserializer: Any | None = None
    fetch_max_wait_ms: int = 500
    fetch_max_bytes: int = 52428800
    fetch_min_bytes: int = 1
    max_partition_fetch_bytes: int = 1 * 1024 * 1024
    request_timeout_ms: int = 40 * 1000
    retry_backoff_ms: int = 100
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    check_crcs: bool = True
    metadata_max_age_ms: int = 5 * 60 * 1000
    max_poll_interval_ms: int = 300000
    rebalance_timeout_ms: Any | None = None
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    consumer_timeout_ms: int = 200
    max_poll_records: Any | None = None
    ssl_context: Any | None = None
    security_protocol: str = "PLAINTEXT"
    api_version: str = "auto"
    exclude_internal_topics: bool = True
    connections_max_idle_ms: int = 540000
    isolation_level: str = "read_uncommitted"
    sasl_mechanism: str = "PLAIN"
    sasl_plain_password: Any | None = None
    sasl_plain_username: Any | None = None
    sasl_kerberos_service_name: str = "kafka"
    sasl_kerberos_domain_name: Any | None = None
    sasl_oauth_token_provider: Any | None = None


class KafkaConsumer(KafkaActions):
    def __init__(self, prefix: str | None = None, kafka_config: KafkaConsumerConfig | None = None) -> None:
        super().__init__(prefix=prefix)
        self.kafka_config = kafka_config or KafkaConsumerConfig()

    async def start(self) -> None:
        self.consumer = aiokafka.consumer.AIOKafkaConsumer(
            *self.get_topics(),
            **self.kafka_config.model_dump(mode="python"),
        )
        await self.consumer.start()
        await self.run()

    async def run(self) -> None:
        async for msg in self.consumer:
            try:
                handler = self.get_handler(msg.topic)
                await handler(msg)

            except Exception:
                logger.exception("Error while processing message:%.*s", 100, str(msg))
                continue

    async def stop(self) -> None:
        await self.consumer.stop()
