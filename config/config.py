import logging
from enum import Enum

class ErrorMessages(Enum):
    SUCCESS = "success"
    FAILED = "failed"

class Kafka(Enum):    
    LOCALHOST = "localhost:9092"