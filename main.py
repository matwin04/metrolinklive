from flask import Flask, render_template, jsonify
import requests
from google.transit import gtfs_realtime_pb2

app = Flask(__name__)

API_KEY = "gMpUXrGPJJ8X9Pp2OivQC1czi046utCMabRM3XQg"
VEHICLE_URL = "https://metrolink-gtfsrt.gbsdigital.us/feed/gtfsrt-vehicles"
TRIP_URL = "https://metrolink-gtfsrt.gbsdigital.us/feed/gtfsrt-trips"

def fetch_gtfs_rt(url):
    headers = {"X-Api-Key": API_KEY}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(r.content)
    return feed

# --- Vehicles ---
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/vehicles")
def vehicles_page():
    feed = fetch_gtfs_rt(VEHICLE_URL)
    vehicles = []
    for entity in feed.entity:
        if entity.HasField("vehicle"):
            v = entity.vehicle
            pos = v.position
            trip = v.trip
            if pos.latitude is not None and pos.longitude is not None:
                vehicles.append({
                    "id": getattr(v.vehicle, "id", "Unknown"),
                    "trip_id": getattr(trip, "trip_id", "Unknown"),
                    "route_id": getattr(trip, "route_id", "Unknown"),
                    "stop_seq": getattr(v, "current_stop_sequence", 0),
                    "lat": pos.latitude,
                    "lon": pos.longitude,
                    "speed": getattr(pos, "speed", 0),
                })
    return render_template("vehicles.html", vehicles=vehicles)

@app.route("/vehicles-data")
def vehicles_data():
    feed = fetch_gtfs_rt(VEHICLE_URL)
    vehicles = []
    for entity in feed.entity:
        if entity.HasField("vehicle"):
            v = entity.vehicle
            pos = v.position
            trip = v.trip
            if pos.latitude is not None and pos.longitude is not None:
                vehicles.append({
                    "id": getattr(v.vehicle, "id", "Unknown"),
                    "trip_id": getattr(trip, "trip_id", "Unknown"),
                    "route_id": getattr(trip, "route_id", "Unknown"),
                    "stop_seq": getattr(v, "current_stop_sequence", 0),
                    "lat": pos.latitude,
                    "lon": pos.longitude,
                    "speed": getattr(pos, "speed", 0),
                })
    return jsonify(vehicles)


# --- Trips ---
@app.route("/trips")
def trips_page():
    feed = fetch_gtfs_rt(TRIP_URL)
    trips = []
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            tu = entity.trip_update
            trips.append({
                "trip_id": tu.trip.trip_id,
                "route_id": tu.trip.route_id,
                "start_time": tu.trip.start_time,
                "start_date": tu.trip.start_date,
                "schedule_relationship": tu.trip.schedule_relationship
            })
    # render static table via template
    return render_template("trips.html", trips=trips)

@app.route("/trips/<trip_id>")
def get_trip(trip_id):
    feed = fetch_gtfs_rt(TRIP_URL)
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            tu = entity.trip_update
            if tu.trip.trip_id == trip_id:
                result = {
                    "trip_id": tu.trip.trip_id,
                    "route_id": tu.trip.route_id,
                    "start_time": tu.trip.start_time,
                    "start_date": tu.trip.start_date,
                    "schedule_relationship": tu.trip.schedule_relationship,
                    "stop_time_updates": [
                        {
                            "stop_id": s.stop_id,
                            "arrival": {
                                "time": s.arrival.time if s.HasField("arrival") and s.arrival.HasField("time") else None,
                                "delay": s.arrival.delay if s.HasField("arrival") and s.arrival.HasField("delay") else None
                            } if s.HasField("arrival") else None,
                            "departure": {
                                "time": s.departure.time if s.HasField("departure") and s.departure.HasField("time") else None,
                                "delay": s.departure.delay if s.HasField("departure") and s.departure.HasField("delay") else None
                            } if s.HasField("departure") else None,
                            "stop_sequence": s.stop_sequence
                        }
                        for s in tu.stop_time_update
                    ]
                }
                return jsonify(result)
    return jsonify({"error": "Trip not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)