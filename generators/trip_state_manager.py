import json
import random
import uuid
from datetime import datetime, timezone
import redis
from faker import Faker
from config.constants import CITY_ZONES, DRIVERS

fake = Faker(['en_IN'])

USERS = [f"U{str(i).zfill(4)}" for i in range(1, 1001)]

class TripStateManager:
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

    def create_trip(self, driver_id, user_id, city):
        zones = list(CITY_ZONES[city].keys())
        pickup_zone = random.choice(zones)
        dropoff_zone = random.choice(zones)

        pickup_coords = CITY_ZONES[city][pickup_zone]
        dropoff_coords = CITY_ZONES[city][dropoff_zone]

        trip = {
            "trip_id": str(uuid.uuid4()),
            "driver_id": driver_id,
            "user_id": user_id,
            "city": city,
            "pickup_zone": pickup_zone,
            "dropoff_zone": dropoff_zone,
            "pickup_lat": round(random.uniform(*pickup_coords["lat"]), 6),
            "pickup_lng": round(random.uniform(*pickup_coords["lng"]), 6),
            "dropoff_lat": round(random.uniform(*dropoff_coords["lat"]), 6),
            "dropoff_lng": round(random.uniform(*dropoff_coords["lng"]), 6),
            "status": "requested",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "accepted_at": None,
            "completed_at": None,
            "cancelled_at": None,
            "surge_multiplier": round(random.uniform(1.0, 3.0), 1),
            "estimated_fare": round(random.uniform(50, 800), 2),
            "estimated_duration_mins": random.randint(5, 60),
            "gps_pings": []
        }

        # Store trip in Redis with 2 hour TTL
        self.redis.setex(
            f"trip:{trip['trip_id']}",
            7200,
            json.dumps(trip)
        )

        # Mark driver as on trip
        self.redis.setex(
            f"driver:{driver_id}:trip",
            7200,
            trip["trip_id"]
        )

        return trip

    def accept_trip(self, trip_id):
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        trip["status"] = "matched"
        trip["accepted_at"] = datetime.now(timezone.utc).isoformat()
        self.redis.setex(f"trip:{trip_id}", 7200, json.dumps(trip))
        return trip

    def complete_trip(self, trip_id):
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        trip["status"] = "completed"
        trip["completed_at"] = datetime.now(timezone.utc).isoformat()
        self.redis.setex(f"trip:{trip_id}", 7200, json.dumps(trip))

        # Free up driver
        self.redis.delete(f"driver:{trip['driver_id']}:trip")

        # Add to completed trips list for payment generator
        self.redis.lpush("completed_trips", trip_id)
        self.redis.expire("completed_trips", 7200)

        return trip

    def cancel_trip(self, trip_id, cancelled_by="user"):
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        trip["status"] = f"cancelled_by_{cancelled_by}"
        trip["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        self.redis.setex(f"trip:{trip_id}", 7200, json.dumps(trip))

        # Free up driver
        self.redis.delete(f"driver:{trip['driver_id']}:trip")
        return trip

    def add_gps_ping(self, trip_id, ping):
        trip = self.get_trip(trip_id)
        if not trip:
            return
        trip["gps_pings"].append(ping)
        self.redis.setex(f"trip:{trip_id}", 7200, json.dumps(trip))

    def get_trip(self, trip_id):
        data = self.redis.get(f"trip:{trip_id}")
        return json.loads(data) if data else None

    def get_driver_trip(self, driver_id):
        trip_id = self.redis.get(f"driver:{driver_id}:trip")
        if not trip_id:
            return None
        return self.get_trip(trip_id)

    def is_driver_on_trip(self, driver_id):
        return self.redis.exists(f"driver:{driver_id}:trip") == 1

    def get_completed_trip(self):
        trip_id = self.redis.rpop("completed_trips")
        if not trip_id:
            return None
        return self.get_trip(trip_id)

    def get_available_driver(self):
        available = [d for d in DRIVERS if not self.is_driver_on_trip(d["driver_id"])]
        return random.choice(available) if available else None