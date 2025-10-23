from flask import Flask, render_template
import requests
from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict

app = Flask(__name__)

API_KEY = "gMpUXrGPJJ8X9Pp2OivQC1czi046utCMabRM3XQg"

def fetch_gtfs_rt(url):
    headers = {"X-Api-Key": API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return MessageToDict(feed)

def trips_to_geojson(feed):
    """Convert trips to GeoJSON features if vehicle locations are available"""
    features = []
    for entity in feed.get("entity", []):
        trip_update = entity.get("tripUpdate")
        if trip_update:
            for stop in trip_update.get("stopTimeUpdate", []):
                stop_id = stop.get("stopId")
                # GTFS-RT trips may not include coordinates, so this is optional
                # You can link stop_id to a stop database with lat/lon if needed
    return {"type": "FeatureCollection", "features": features}

def vehicles_to_geojson(feed):
    """Convert vehicles to GeoJSON features"""
    features = []
    for entity in feed.get("entity", []):
        vehicle = entity.get("vehicle")
        if vehicle:
            pos = vehicle.get("position")
            if pos:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [pos["longitude"], pos["latitude"]]
                    },
                    "properties": {
                        "id": vehicle.get("vehicle", {}).get("id"),
                        "trip_id": vehicle.get("trip", {}).get("tripId"),
                        "route_id": vehicle.get("trip", {}).get("routeId"),
                        "current_stop_sequence": vehicle.get("currentStopSequence")
                    }
                })
    return {"type": "FeatureCollection", "features": features}
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/gtfsrt/trips")
def gtfsrt_trips():
    feed = fetch_gtfs_rt("https://metrolink-gtfsrt.gbsdigital.us/feed/gtfsrt-trips")
    geojson = trips_to_geojson(feed)
    return render_template("gtfsrt_trips.html", feed=feed, geojson=geojson)

@app.route("/gtfsrt/vehicles")
def gtfsrt_vehicles():
    feed = fetch_gtfs_rt("https://metrolink-gtfsrt.gbsdigital.us/feed/gtfsrt-vehicles")
    geojson = vehicles_to_geojson(feed)
    return render_template("vehicles.html", feed=feed, geojson=geojson)

if __name__ == "__main__":
    app.run(debug=True)