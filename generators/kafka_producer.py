from kafka import KafkaProducer
import json

class DataCrunchProducer:
    def __init__(self, topic):
        self.topic = topic
        self.producer = KafkaProducer()
    
    def send_message(self, key, value):
        pass
    
    def close(self):
        pass