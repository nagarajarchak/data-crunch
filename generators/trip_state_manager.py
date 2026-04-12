import json
import random
import uuid
from datetime import datetime, timezone
import redis
from faker import Faker

fake = Faker(['en_IN'])

USERS = [f"U{str(i).zfill(4)}" for i in range(1, 1001)]

# City zones with real coordinates
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