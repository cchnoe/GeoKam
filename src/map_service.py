import json
import sys
from math import sqrt, radians, sin, cos, atan2
from pathlib import Path
import threading

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

    def __init__(self):
        self.routes_dir = Path("routes")
        self.routes_dir.mkdir(exist_ok=True)
        self.consolidated_file = self.routes_dir / "rutas_consolidadas.xlsx"
        self.lock = threading.Lock()  # Para acceso thread-safe

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula la distancia en kilómetros entre dos puntos usando la fórmula de Haversine."""
        R = 6371  # Radio de la Tierra en kilómetros

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def calculate_route_stats(self, route_df: pd.DataFrame, lat_col: str = None, lon_col: str = None) -> dict:
        """Calcula estadísticas de la ruta: distancia total y tiempo estimado."""
        if route_df.empty:
            return {"distancia_km": 0, "tiempo_estimado_horas": 0, "tiempo_estimado_minutos": 0}

        # Detectar automáticamente las columnas de coordenadas si no se especifican
        if lat_col is None or lon_col is None:
            possible_lat_cols = ['num_latitud', 'latitud', 'latitude', 'lat']
            possible_lon_cols = ['num_longitud', 'longitud', 'longitude', 'lon', 'lng']

            lat_col = next((col for col in possible_lat_cols if col in route_df.columns), None)
            lon_col = next((col for col in possible_lon_cols if col in route_df.columns), None)

        if lat_col is None or lon_col is None or lat_col not in route_df.columns or lon_col not in route_df.columns:
            return {"distancia_km": 0, "tiempo_estimado_horas": 0, "tiempo_estimado_minutos": 0}

        # Calcular distancia total
        total_distance = 0
        coords = route_df[[lat_col, lon_col]].apply(pd.to_numeric, errors='coerce').dropna()

        if len(coords) < 2:
            # Si hay menos de 2 puntos, no hay distancia que calcular
            total_distance = 0
        else:
            for i in range(len(coords) - 1):
                lat1, lon1 = coords.iloc[i]
                lat2, lon2 = coords.iloc[i + 1]
                # Verificar que las coordenadas sean válidas
                if pd.notna(lat1) and pd.notna(lon1) and pd.notna(lat2) and pd.notna(lon2):
                    total_distance += self.haversine_distance(lat1, lon1, lat2, lon2)

        # Estimar tiempo: asumiendo 30 km/h promedio en ciudad + tiempo de visita por punto (15 min)
        velocidad_promedio_kmh = 30  # km/h
        tiempo_viaje_horas = total_distance / velocidad_promedio_kmh if velocidad_promedio_kmh > 0 else 0
        tiempo_visita_horas = len(route_df) * 0.25  # 15 minutos por punto = 0.25 horas

        # Si no hay distancia calculada pero hay puntos, estimar una distancia aproximada
        if total_distance == 0 and len(route_df) > 1:
            # Estimación aproximada: asumir 2 km entre puntos consecutivos en promedio para ciudad
            total_distance = (len(route_df) - 1) * 2.0  # 2 km por segmento
            tiempo_viaje_horas = total_distance / velocidad_promedio_kmh

        tiempo_total_horas = tiempo_viaje_horas + tiempo_visita_horas
        tiempo_total_minutos = tiempo_total_horas * 60

        return {
            "distancia_km": round(total_distance, 2),
            "tiempo_estimado_horas": round(tiempo_total_horas, 1),
            "tiempo_estimado_minutos": round(tiempo_total_minutos)
        }

    def generate_route(self, df: pd.DataFrame, lat_col: str = "num_latitud", lon_col: str = "num_longitud") -> tuple[pd.DataFrame, list[int]]:
        """Genera un ranking de visita usando algoritmo de vecino más cercano."""
        if df.empty:
            return df.copy(), []

        if lat_col not in df.columns or lon_col not in df.columns:
            st.error(f"Columnas '{lat_col}' o '{lon_col}' no encontradas en los datos.")
            return df.copy(), []

        # Preparar datos, mantener todas las columnas
        route_df = df.copy().dropna(subset=[lat_col, lon_col])
        if route_df.empty:
            st.warning("No hay datos con coordenadas válidas para generar ruta.")
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

        # Guardar la ruta generada
        self.save_route(ordered_df, lat_col, lon_col)

        return ordered_df, route

    def save_route(self, route_df: pd.DataFrame, lat_col: str, lon_col: str) -> None:
        """Guarda la ruta en el archivo consolidado Excel."""
        with self.lock:  # Thread-safe
            try:
                # Verificar que openpyxl esté disponible
                try:
                    import openpyxl
                except ImportError:
                    raise Exception("El módulo 'openpyxl' no está instalado. Instale con: pip install openpyxl")

                # Preparar datos para guardar
                save_df = route_df.copy()
                save_df['fecha_generacion'] = pd.Timestamp.now()
                save_df['route_id'] = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

                # Columnas a guardar
                cols_to_save = ['route_id', 'rank', 'fecha_generacion']
                if 'kam' in save_df.columns:
                    cols_to_save.append('kam')
                if 'nbr_direccion' in save_df.columns:
                    cols_to_save.append('nbr_direccion')
                if 'grupo_economico' in save_df.columns:
                    cols_to_save.append('grupo_economico')
                if lat_col in save_df.columns:
                    cols_to_save.append(lat_col)
                if lon_col in save_df.columns:
                    cols_to_save.append(lon_col)

                save_data = save_df[cols_to_save]

                # Leer archivo existente o crear nuevo
                if self.consolidated_file.exists():
                    try:
                        existing_df = pd.read_excel(self.consolidated_file, engine='openpyxl')
                        combined_df = pd.concat([existing_df, save_data], ignore_index=True)
                    except Exception as e:
                        st.warning(f"Error leyendo archivo existente: {e}. Creando nuevo archivo.")
                        combined_df = save_data
                else:
                    combined_df = save_data

                # Guardar archivo consolidado
                with pd.ExcelWriter(self.consolidated_file, engine='openpyxl') as writer:
                    combined_df.to_excel(writer, sheet_name='Rutas', index=False)

            except Exception as e:
                st.error(f"Error guardando ruta consolidada: {e}")
                # Fallback: guardar como CSV individual
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                kam_name = str(route_df['kam'].iloc[0]) if 'kam' in route_df.columns and not route_df['kam'].empty else ""
                filename = f"route_{kam_name}_{timestamp}.csv" if kam_name else f"route_{timestamp}.csv"
                filepath = self.routes_dir / filename
                route_df.to_csv(filepath, index=False)
                st.warning(f"Ruta guardada como archivo individual: {filename}")

    def list_saved_routes(self) -> list[str]:
        """Lista las rutas guardadas desde el archivo consolidado."""
        if not self.consolidated_file.exists():
            return []

        try:
            df = pd.read_excel(self.consolidated_file, engine='openpyxl')
            if df.empty:
                return []

            # Agrupar por route_id y obtener información de cada ruta
            routes_info = []
            for route_id, group in df.groupby('route_id'):
                if len(group) > 0:
                    routes_info.append(str(route_id))

            return sorted(routes_info, reverse=True)  # Más recientes primero

        except Exception as e:
            st.error(f"Error leyendo rutas consolidadas: {e}")
            return []

    def load_route(self, route_name: str) -> pd.DataFrame:
        """Carga una ruta específica desde el archivo consolidado."""
        if not self.consolidated_file.exists():
            return pd.DataFrame()

        try:
            df = pd.read_excel(self.consolidated_file, engine='openpyxl')
            if df.empty:
                return pd.DataFrame()

            route_id = str(route_name)
            if route_id not in df['route_id'].astype(str).values:
                # Si no coincide directamente, buscar último componente numérico
                parts = route_name.split('_')
                for part in reversed(parts):
                    if part.isdigit():
                        route_id = part
                        break

            route_df = df[df['route_id'].astype(str) == route_id].copy()
            return route_df

        except Exception as e:
            st.error(f"Error cargando ruta {route_name}: {e}")
            return pd.DataFrame()

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
