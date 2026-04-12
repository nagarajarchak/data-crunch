from generators.trip_state_manager import TripStateManager

tsm = TripStateManager()

# Create a trip
trip = tsm.create_trip(
    driver_id="D0001",
    user_id="U0001",
    city="Bangalore"
)
print(f"Created trip: {trip['trip_id']}")
print(f"Status: {trip['status']}")

# Check driver is on trip
print(f"Driver on trip: {tsm.is_driver_on_trip('D0001')}")

# Accept trip
tsm.accept_trip(trip['trip_id'])
print(f"Trip accepted!")

# Complete trip
tsm.complete_trip(trip['trip_id'])
print(f"Trip completed!")

# Check driver is free
print(f"Driver on trip: {tsm.is_driver_on_trip('D0001')}")