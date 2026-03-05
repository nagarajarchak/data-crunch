import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCrunchProducer:
    def __init__(self, topic):
        self.topic = topic
        self.dlq_topic = "dead-letter-queue"
        
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            acks=1,
            batch_size=16384,
            linger_ms=10,
            compression_type='snappy',
            retries=3,
            key_serializer=lambda k: str(k).encode('utf-8'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info(f"Producer initialized for topic: {self.topic}")

    def send_message(self, key, value):
        try:
            future = self.producer.send(
                self.topic,
                key=key,
                value=value
            )
            future.get(timeout=10)
        except KafkaError as e:
            logger.error(f"Failed to send message to {self.topic}: {e}")
            self._send_to_dlq(key, value, str(e))

    def _send_to_dlq(self, key, value, error):
        try:
            dlq_message = {
                "original_topic": self.topic,
                "original_key": str(key),
                "original_value": value,
                "error": error
            }
            self.producer.send(
                self.dlq_topic,
                key=key,
                value=dlq_message
            )
            logger.warning(f"Message sent to DLQ: {error}")
        except KafkaError as e:
            logger.error(f"Failed to send to DLQ: {e}")

    def flush(self):
        self.producer.flush()

    def close(self):
        self.producer.flush()
        self.producer.close()
        logger.info(f"Producer closed for topic: {self.topic}")