from types import TracebackType
from typing import Any, AnyStr, Self

import aiokafka
from pydantic import BaseModel


class KafkaProducerConfig(BaseModel):
    loop: Any | None = None
    bootstrap_servers: str = "localhost"
    client_id: Any | None = None
    metadata_max_age_ms: int = 300000
    request_timeout_ms: int = 40000
    api_version: str = "auto"
    key_serializer: Any | None = None
    value_serializer: Any | None = None
    compression_type: Any | None = None
    max_batch_size: int = 16384
    max_request_size: int = 1048576
    linger_ms: int = 0
    retry_backoff_ms: int = 100
    security_protocol: str = "PLAINTEXT"
    ssl_context: Any | None = None
    connections_max_idle_ms: int = 540000
    enable_idempotence: bool = False
    transactional_id: Any | None = None
    transaction_timeout_ms: int = 60000
    sasl_mechanism: str = "PLAIN"
    sasl_plain_password: Any | None = None
    sasl_plain_username: Any | None = None
    sasl_kerberos_service_name: str = "kafka"
    sasl_kerberos_domain_name: Any | None = None
    sasl_oauth_token_provider: Any | None = None


class KafkaProducer:
    def __init__(self, kafka_config: KafkaProducerConfig | None = None) -> None:
        self.kafka_config = kafka_config or KafkaProducerConfig()
        self.producer = aiokafka.producer.AIOKafkaProducer(**self.kafka_config.model_dump(mode="python"))

    async def start(self) -> None:
        await self.producer.start()

    async def stop(self) -> None:
        await self.producer.stop()

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(
        self,
        typ: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def send(self, topic: str, message: AnyStr) -> None:
        await self.producer.send(topic=topic, value=message if isinstance(message, bytes) else message.encode())
