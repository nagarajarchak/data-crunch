from enum import Enum

class Kafka(Enum):    
    LOCALHOST = "localhost"
    PORT = "9092"
    DLQ = "dead-letter-queue"
    