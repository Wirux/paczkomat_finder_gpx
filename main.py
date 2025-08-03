
import gpxpy
import requests
import folium
from geopy.distance import geodesic
from typing import List, Tuple, Dict
import time



# === Configuration ===
GPX_FILE = "trail_gsb.gpx"
TOKEN_FILE = "inpost.token"
TRAIL_CHUNK = 500
SEARCH_RADIUS_KM = 2
DISTANCE_MARKERS_EACH = 10
REQUEST_DELAY_SECONDS = 0.1
MAP_OUTPUT_FILE = "output_map.html"


def load_token_from_file(token_path: str) -> str:
    """Read API token from a text file."""
    with open(token_path, 'r') as file:
        return file.read().strip()


def get_distance_markers(gpx_path: str, interval_km: float) -> List[Tuple[float, float, float]]:
    """
    Return a list of (lat, lon, distance_km) every `interval_km` along the GPX path.
    """
    with open(gpx_path, 'r') as f:
        gpx = gpxpy.parse(f)

    all_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            all_points.extend(segment.points)

    if not all_points:
        return []

    markers = []
    total_distance = 0.0
    last_point = all_points[0]

    for point in all_points[1:]:
        segment_distance = geodesic(
            (last_point.latitude, last_point.longitude),
            (point.latitude, point.longitude)
        ).km
        total_distance += segment_distance

        if len(markers) == 0 or total_distance - markers[-1][2] >= interval_km:
            markers.append((point.latitude, point.longitude, round(total_distance)))

        last_point = point

    return markers

def parse_gpx_points_every_n_km(gpx_path: str, interval_km: float) -> List[Tuple[float, float]]:
    """
    Load GPX track and extract points approximately every `interval_km`.
    """
    with open(gpx_path, 'r') as f:
        gpx = gpxpy.parse(f)

    all_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            all_points.extend(segment.points)

    if not all_points:
        return []

    sampled_points = [all_points[0]]
    last_added = all_points[0]

    distance_accumulator = 0.0

    for point in all_points[1:]:
        segment_distance = geodesic(
            (last_added.latitude, last_added.longitude),
            (point.latitude, point.longitude)
        ).km

        distance_accumulator += segment_distance

        if distance_accumulator >= interval_km:
            sampled_points.append(point)
            last_added = point
            distance_accumulator = 0.0

    return [(p.latitude, p.longitude) for p in sampled_points]

def get_nearby_parcel_lockers(
    lat: float,
    lon: float,
    radius_km: float,
    token: str
) -> List[Dict]:
    """
    Query InPost API for parcel lockers near a location using `relative_point` and `max_distance`.
    Includes verbose debug logging.
    """
    url = "https://api-shipx-pl.easypack24.net/v1/points"
    relative_point = f"{lat:.6f},{lon:.6f}"
    params = {
        "type": "parcel_locker",
        "relative_point": relative_point,
        "max_distance": int(radius_km * 1000),  # meters
        "sort": "distance"
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    # print(f"[DEBUG] GET {url}")
    # print(f"[DEBUG] Params: {params}")
    # print(f"[DEBUG] Headers: {headers}")

    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"[DEBUG] Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            # print(f"[DEBUG] Returned lockers: {data}")
            return data
        else:
            print(f"[ERROR] Failed with status code {response.status_code}")
            print(f"[ERROR] Response content: {response.text}")
            return []
    except requests.RequestException as e:
        print(f"[EXCEPTION] Request error: {e}")
        return []

def create_map_with_lockers(
    route_points: List[Tuple[float, float]],
    lockers: List[Dict],
    distance_markers: List[Tuple[float, float, float]]
) -> folium.Map:
    """
    Create a folium map with the route, parcel locker markers, and distance labels.
    """
    center_latlon = route_points[len(route_points) // 2]
    map_obj = folium.Map(location=center_latlon, zoom_start=10)

    # Draw the trail
    folium.PolyLine(route_points, color="blue", weight=3).add_to(map_obj)

    # Add parcel locker markers
    for locker in lockers:
        loc = locker["location"]
        folium.Marker(
            [loc["latitude"], loc["longitude"]],
            popup=f"{locker['name']}<br>{locker.get('location_description', '')}",
            icon=folium.Icon(color='green', icon='inbox', prefix='fa')
        ).add_to(map_obj)

    # Add distance markers (e.g., "5 km", "10 km")
    for lat, lon, distance_km in distance_markers:
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html=f"""<div style="font-size: 10pt; color: black;">{int(distance_km)} km</div>""")
        ).add_to(map_obj)

    return map_obj

def main():
    print("[1/4] Loading API token...")
    token = load_token_from_file(TOKEN_FILE)

    print("[2/4] Parsing GPX route...")
    route_points = parse_gpx_points_every_n_km(GPX_FILE, TRAIL_CHUNK)
    print(len(route_points))

    print("[3/4] Fetching parcel lockers from InPost...")
    all_lockers = []
    for index, (lat, lon) in enumerate(route_points):
        print(f"[INFO] Processing point {index + 1}/{len(route_points)} at ({lat:.5f}, {lon:.5f})")
        lockers = get_nearby_parcel_lockers(lat, lon, SEARCH_RADIUS_KM, token)
        all_lockers.extend(lockers.get("items", []))
        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"   => Found {len(all_lockers)} lockers, filtering unique ones...")
    print(all_lockers)
    seen = set()
    unique_lockers = []
    for locker in all_lockers:
        if locker["name"] not in seen:
            unique_lockers.append(locker)
            seen.add(locker["name"])

    print("[INFO] Generating distance markers...")
    distance_markers = get_distance_markers(GPX_FILE, DISTANCE_MARKERS_EACH )  
    print(f"[4/4] Creating map with {len(unique_lockers)} unique parcel lockers...")
    result_map = create_map_with_lockers(route_points, unique_lockers, distance_markers)
    result_map.save(MAP_OUTPUT_FILE)

    print(f"✔ Map saved to: {MAP_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
