import json
from math import sqrt

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

    def generate_route(self, df: pd.DataFrame, lat_col: str = "num_latitud", lon_col: str = "num_longitud") -> tuple[pd.DataFrame, list[int]]:
        """Genera un ranking de visita usando algoritmo de vecino más cercano."""
        if df.empty:
            return df.copy(), []

        # Preparar datos, mantener todas las columnas
        route_df = df.copy().dropna(subset=[lat_col, lon_col])
        if route_df.empty:
            return df.copy(), []

        # Algoritmo de vecino más cercano
        points = route_df[[lat_col, lon_col]].to_dict('records')
        n = len(points)
        visited = [False] * n
        route = [0]  # Empezar desde el primer punto
        visited[0] = True

        for _ in range(1, n):
            last = route[-1]
            min_dist = float('inf')
            next_point = -1
            for i in range(n):
                if not visited[i]:
                    dist = sqrt((points[i][lat_col] - points[last][lat_col])**2 + (points[i][lon_col] - points[last][lon_col])**2)
                    if dist < min_dist:
                        min_dist = dist
                        next_point = i
            if next_point != -1:
                route.append(next_point)
                visited[next_point] = True

        # Reordenar DataFrame según la ruta y agregar ranking
        ordered_df = route_df.iloc[route].copy().reset_index(drop=True)
        ordered_df['rank'] = range(1, len(ordered_df) + 1)

        return ordered_df, route

    def show_route_map(
        self,
        df: pd.DataFrame,
        lat_col: str = "num_latitud",
        lon_col: str = "num_longitud",
        height: int = 600,
    ) -> None:
        if df.empty or 'rank' not in df.columns:
            st.info("No hay ruta para mostrar.")
            return

        # Renombrar para consistencia
        map_df = df.rename(columns={lat_col: "lat", lon_col: "lon"})
        points = map_df[["lat", "lon", "rank"]].to_dict(orient="records")
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
      const latlngs = [];
      points.forEach((pt, index) => {{
        const latlng = [pt.lat, pt.lon];
        latlngs.push(latlng);

        // Agregar marcador con número
        L.marker(latlng, {{
          icon: L.divIcon({{
            className: 'custom-div-icon',
            html: '<div style="background-color: #ff0000; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-weight: bold;">' + pt.rank + '</div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          }})
        }}).addTo(map);
      }});

      // Dibujar línea conectando los puntos
      L.polyline(latlngs, {{
        color: 'blue',
        weight: 3,
        opacity: 0.7
      }}).addTo(map);
    }}
  </script>
</body>
</html>
"""

        components.html(html, height=height, width=height)


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
