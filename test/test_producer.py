from config.kafka import Topics
from generators.kafka_producer import DataCrunchProducer

producer = DataCrunchProducer(Topics.GPS_PINGS.value)
producer.send_message(
    key="D001",
    value={"driver_id": "D001", "lat": 12.9716, "lng": 77.5946, "speed": 45.2}
)
producer.close()
