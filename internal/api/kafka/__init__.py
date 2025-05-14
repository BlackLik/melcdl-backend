from internal.client.kafka.consumer import KafkaActions

from . import melanoma

actions = KafkaActions()

actions.include_action(melanoma.actions)
