from enum import Enum

class Kafka(Enum):    
    LOCALHOST = "localhost"
    PORT = "9092"
    DLQ = "dead-letter-queue"
    COMPRESSION_SNAPPY = "snappy"
    UTF8_ENCODING = "utf-8"
    