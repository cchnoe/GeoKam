import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


class MapService:
    PERU_BOUNDS = {
        "south": -18.35,
        "north": 0.08,
        "west": -81.35,
        "east": -68.64,
    }

    def show_points_map(
        self,
        df: pd.DataFrame,
        lat_col: str = "num_latitud",
        lon_col: str = "num_longitud",
        height: int = 1200,
    ) -> None:
        if lat_col not in df.columns or lon_col not in df.columns:
            st.info("No hay latitud/longitud para mostrar en el mapa.")
            return

        map_df = df[[lat_col, lon_col]].copy()
        map_df[lat_col] = pd.to_numeric(map_df[lat_col], errors="coerce")
        map_df[lon_col] = pd.to_numeric(map_df[lon_col], errors="coerce")
        map_df = map_df.dropna(subset=[lat_col, lon_col]).rename(columns={lat_col: "lat", lon_col: "lon"})

        if map_df.empty:
            st.info("No hay coordenadas válidas para mostrar en el mapa.")
            return

        points = map_df.to_dict(orient="records")
        south = float(max(map_df["lat"].min(), self.PERU_BOUNDS["south"]))
        north = float(min(map_df["lat"].max(), self.PERU_BOUNDS["north"]))
        west = float(max(map_df["lon"].min(), self.PERU_BOUNDS["west"]))
        east = float(min(map_df["lon"].max(), self.PERU_BOUNDS["east"]))

        if south >= north or west >= east:
            south = self.PERU_BOUNDS["south"]
            north = self.PERU_BOUNDS["north"]
            west = self.PERU_BOUNDS["west"]
            east = self.PERU_BOUNDS["east"]

        bounds = [[south, west], [north, east]]
        data_json = json.dumps(points)

        html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
  <style>
    html, body {{ margin: 0; padding: 0; height: 100%; }}
    #map {{ width: 100%; height: 100%; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <script>
    const points = {data_json};
    const map = L.map('map').fitBounds({bounds});
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }}).addTo(map);

    if (points.length > 0) {{
      const markers = points.map(pt => L.circleMarker([pt.lat, pt.lon], {{
        radius: 5,
        fillColor: '#ff0000',
        color: '#770000',
        weight: 1,
        opacity: 0.9,
        fillOpacity: 0.8,
      }}).addTo(map));

      const featureGroup = L.featureGroup(markers);
      map.fitBounds(featureGroup.getBounds().pad(0.15));
    }}
  </script>
</body>
</html>
"""

        components.html(html, height=height, width=height)
