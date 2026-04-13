import uuid
import random
import time
from datetime import datetime, timezone, timedelta
from faker import Faker
from generators.kafka_producer import DataCrunchProducer
from config.kafka import Topics

fake = Faker(['en_IN'])

CITY_ZONES = {
    "Bangalore": {
        "Koramangala": {"lat": (12.9247, 12.9447), "lng": (77.6142, 77.6342)},
        "Indiranagar": {"lat": (12.9716, 12.9916), "lng": (77.6384, 77.6584)},
        "Whitefield": {"lat": (12.9698, 12.9898), "lng": (77.7499, 77.7699)},
        "Electronic City": {"lat": (12.8399, 12.8599), "lng": (77.6699, 77.6899)},
        "HSR Layout": {"lat": (12.9081, 12.9281), "lng": (77.6367, 77.6567)},
    },
    "Mumbai": {
        "Bandra": {"lat": (19.0496, 19.0696), "lng": (72.8356, 72.8556)},
        "Andheri": {"lat": (19.1136, 19.1336), "lng": (72.8467, 72.8667)},
        "Powai": {"lat": (19.1174, 19.1374), "lng": (72.9054, 72.9254)},
        "BKC": {"lat": (19.0596, 19.0796), "lng": (72.8656, 72.8856)},
        "Juhu": {"lat": (19.0883, 19.1083), "lng": (72.8263, 72.8463)},
    },
    "Delhi": {
        "Connaught Place": {"lat": (28.6289, 28.6489), "lng": (77.2065, 77.2265)},
        "Gurgaon": {"lat": (28.4595, 28.4795), "lng": (77.0266, 77.0466)},
        "Noida": {"lat": (28.5355, 28.5555), "lng": (77.3910, 77.4110)},
        "Hauz Khas": {"lat": (28.5431, 28.5631), "lng": (77.1964, 77.2164)},
        "Dwarka": {"lat": (28.5733, 28.5933), "lng": (77.0468, 77.0668)},
    },
    "Hyderabad": {
        "Hitech City": {"lat": (17.4374, 17.4574), "lng": (78.3762, 78.3962)},
        "Gachibowli": {"lat": (17.4401, 17.4601), "lng": (78.3489, 78.3689)},
        "Banjara Hills": {"lat": (17.4126, 17.4326), "lng": (78.4272, 78.4472)},
        "Jubilee Hills": {"lat": (17.4229, 17.4429), "lng": (78.4063, 78.4263)},
        "Secunderabad": {"lat": (17.4399, 17.4599), "lng": (78.4983, 78.5183)},
    },
    "Chennai": {
        "Anna Nagar": {"lat": (13.0849, 13.1049), "lng": (80.2099, 80.2299)},
        "T Nagar": {"lat": (13.0389, 13.0589), "lng": (80.2311, 80.2511)},
        "OMR": {"lat": (12.9010, 12.9210), "lng": (80.2279, 80.2479)},
        "Velachery": {"lat": (12.9750, 12.9950), "lng": (80.2176, 80.2376)},
        "Adyar": {"lat": (13.0012, 13.0212), "lng": (80.2565, 80.2765)},
    }
}

VEHICLE_TYPES = ["bike", "auto", "mini_cab", "sedan", "suv"]
TRIP_STATUSES = ["available", "en_route_to_pickup", "on_trip", "idle", "offline"]

# Generate pool of drivers
DRIVERS = [
    {
        "driver_id": f"D{str(i).zfill(4)}",
        "city": random.choice(list(CITY_ZONES.keys())),
        "vehicle_type": random.choice(VEHICLE_TYPES),
        "name": fake.name()
    }
    for i in range(1, 501)
]


class GPSGenerator:
    def __init__(self):
        self.producer = DataCrunchProducer(Topics.GPS_PINGS.value)
        self.fake = Faker(['en_IN'])

    def _random_coords(self, city, zone):
        zone_data = CITY_ZONES[city][zone]
        lat = round(random.uniform(*zone_data["lat"]), 6)
        lng = round(random.uniform(*zone_data["lng"]), 6)
        return lat, lng

    def generate_ping(self, driver):
        city = driver["city"]
        zone = random.choice(list(CITY_ZONES[city].keys()))
        lat, lng = self._random_coords(city, zone)

        ping = {
            "event_id": str(uuid.uuid4()),
            "driver_id": driver["driver_id"],
            "trip_id": str(uuid.uuid4()),
            "latitude": lat,
            "longitude": lng,
            "speed_kmph": round(random.uniform(0, 80), 1),
            "heading": random.randint(0, 360),
            "altitude": round(random.uniform(800, 950), 1),
            "accuracy": round(random.uniform(2, 10), 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": random.choice(TRIP_STATUSES),
            "vehicle_type": driver["vehicle_type"],
            "city": city,
            "zone": zone
        }

        return self.inject_messiness(ping)

    def inject_messiness(self, ping):
        r = random.random()

        # Duplicate event (~2%)
        if r < 0.02:
            ping["event_id"] = ping["event_id"]

        # Null coordinates (~0.5%)
        elif r < 0.025:
            ping["latitude"] = None
            ping["longitude"] = None

        # Impossible speed (~0.5%)
        elif r < 0.03:
            ping["speed_kmph"] = random.uniform(250, 400)

        # Missing driver_id (~1%)
        elif r < 0.04:
            ping["driver_id"] = None

        # Out of order timestamp (~3%)
        elif r < 0.07:
            past = datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 30))
            ping["timestamp"] = past.isoformat()

        # Wrong data type - speed as string (~1%)
        elif r < 0.08:
            ping["speed_kmph"] = str(ping["speed_kmph"])

        return ping

    def run(self):
        print(f"Starting GPS generator for {len(DRIVERS)} drivers...")
        try:
            while True:
                for driver in DRIVERS:
                    ping = self.generate_ping(driver)
                    self.producer.send_message(
                        key=ping.get("driver_id", "unknown"),
                        value=ping
                    )
                time.sleep(3)
        except KeyboardInterrupt:
            print("Stopping GPS generator...")
            self.producer.close()


if __name__ == "__main__":
    generator = GPSGenerator()
    generator.run()