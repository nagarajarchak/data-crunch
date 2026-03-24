from enum import Enum

class ErrorMessages(Enum):
    SUCCESS = "success"
    FAILED = "failed"

class Kafka(Enum):    
    LOCALHOST = "localhost"
    PORT = "9092"
    DLQ = "dead-letter-queue"