from enum import Enum

class General(Enum):    
    LOCALHOST = "localhost"
    PORT = "9092"
    COMPRESSION_SNAPPY = "snappy"
    UTF8_ENCODING = "utf-8"
    
class Topics(Enum):
    DLQ = "dead-letter-queue"
    APP_LOGS = "app-logs"
    DRIVER_BEHAVIOR = "driver-behavior"
    GPS_PINGS = "gps-pings"
    PAYMENTS = "payments"
    RIDE_REQUESTS = "ride-requests"