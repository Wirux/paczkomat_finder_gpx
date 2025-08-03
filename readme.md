
# 📦 InPost Parcel Lockers Near GPX Trail + Distance Markers Map

This Python script allows you to:
- Parse a GPX trail (e.g., a hiking route),
- Find nearby **InPost parcel lockers** along the trail using the InPost API,
- Display the route and nearby lockers on an interactive **HTML map**,
- Add **distance markers** (e.g., every 1 km) to the trail.

---

## 🚀 Features

- GPX trail parsing using [`gpxpy`](https://github.com/tkrajina/gpxpy)
- Locker search via the [InPost ShipX API](https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/18153493/Points+Parcel+Locker+ParcelPoint)
- Interactive map with [Folium](https://python-visualization.github.io/folium/)
- Distance markers every X kilometers

---

## 📁 File Structure

- `trail_gsb.gpx` – your GPX file with the trail
- `inpost.token` – your InPost API token (see below)
- `output_map.html` – output map with trail, lockers, and markers
- `main.py` – main script (see usage)
- `README.md` – this file

---

## 🔐 InPost API Token Setup

1. Go to the official InPost API documentation and register your application:  
   👉 [Points Parcel Locker / ParcelPoint API Manual](https://dokumentacja-inpost.atlassian.net/wiki/spaces/PL/pages/18153493/Points+Parcel+Locker+ParcelPoint)

2. Generate a token (Bearer Token) according to their documentation.

3. Save your token string into a file called `inpost.token` (no extra spaces or newlines):

