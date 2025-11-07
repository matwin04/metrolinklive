const map = new maplibregl.Map({
    container: "map",
    style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    center: [-118.25, 34.05],
    zoom: 8,
});

// Define colors per route
const routeColors = {
    "Orange County Line": "#DE620D",
    "San Bernardino Line": "#0000FF",
    "Ventura County Line": "#00FF00",
    "Riverside Line": "#FFA500",
    "91 Line": "#165D9B"
    // add more routes if needed
};

map.on('load', () => {
    map.addSource('vehicles', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
    });
    map.addSource("stations", {
        type: "geojson",
        data: "/static/maps/CA_Stations.geojson"
    });
     map.addSource("routes", {
            type: "geojson",
            data: "/static/maps/ML_Routes.geojson"
     });



    map.addLayer({
        id: 'vehicle-dots',
        type: 'circle',
        source: 'vehicles',
        paint: {
            'circle-radius': 5,
            'circle-color': ['get', 'color'],  // get color from feature property
            'circle-stroke-width': 1,
            'circle-stroke-color': '#fff'
        }
    });


        // --- STATION LAYER ---
        map.addLayer({
            id: "stations-layer",
            type: "circle",
            source: "stations",
            paint: {
                "circle-radius": 3,
                "circle-color": "#000000",
                "circle-stroke-width": 1,
                "circle-stroke-color": "#fff"
            }
        });
    map.on('click', 'vehicle-dots', (e) => {
        const props = e.features[0].properties;
        new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(`
                <strong>Train ${props.id}</strong><br>
                Route: ${props.route}<br>
                Trip: <a href="/trips/${props.trip}">${props.trip}</a><br>
                Speed: ${Number(props.speed).toFixed(1)} m/s
            `)
            .addTo(map);
    });

    map.on('mouseenter', 'vehicle-dots', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'vehicle-dots', () => map.getCanvas().style.cursor = '');

    // Start fetching vehicle data every 30 seconds
    updateVehicles();
    setInterval(updateVehicles, 30000);
});

function updateVehicles() {
    fetch('/vehicles-data')
        .then(resp => resp.json())
        .then(data => {
            const geojson = {
                type: "FeatureCollection",
                features: data
                    .filter(v => v.lat && v.lon)
                    .map(v => ({
                        type: "Feature",
                        geometry: { type: "Point", coordinates: [v.lon, v.lat] },
                        properties: {
                            id: v.id,
                            trip: v.trip_id,
                            route: v.route_id,
                            speed: v.speed,
                            color: routeColors[v.route_id] || "#FF0000" // default red
                        }
                    }))
            };
            map.getSource('vehicles').setData(geojson);
        });
}