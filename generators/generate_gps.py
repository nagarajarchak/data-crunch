import uuid
import random
import time
from datetime import datetime, timezone, timedelta
from faker import Faker
from generators.kafka_producer import DataCrunchProducer
from config.kafka import Topics
from config.constants import CITY_ZONES, TRIP_STATUSES, DRIVERS, fake


class GPSGenerator:
    def __init__(self):
        self.producer = DataCrunchProducer(Topics.GPS_PINGS.value)
        self.fake = fake

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