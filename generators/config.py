import logging
from enum import Enum

class Config(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    LOCALHOST = "localhost:9092"