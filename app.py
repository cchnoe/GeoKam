import streamlit as st
import pandas as pd

from src.data_service import DataService
from src.filter_service import FilterService
from src.map_service import MapService
from src.ui_service import UIService


class ComercioGeoApp:
    def __init__(self):
        self.data_service = DataService()
        self.filter_service = FilterService()
        self.map_service = MapService()
        self.ui_service = UIService()

    def run(self):
        st.set_page_config(page_title="Filtro de comercios", layout="wide")
        st.title("Filtro de comercios por jerarquía comercial")
        st.caption("Selecciona múltiples valores por nivel y marca direcciones específicas.")

        df = self.data_service.load_data()

        if df.empty:
            st.warning("No se encontró información para mostrar.")
            return

        df = self.data_service.standardize_columns(df)

        st.subheader("Vista general")
        c1, c2, c3 = st.columns(3)
        c1.metric("Registros", len(df))
        c2.metric("Grupos económicos", df["grupo_economico"].nunique(dropna=True))
        c3.metric("KAMs", df["kam"].nunique(dropna=True))

        selected_kam = st.sidebar.multiselect(
            "KAM",
            self.filter_service.get_options(df, "kam"),
            key="kam"
        )
        df_kam = self.filter_service.filter_by_values(df, "kam", selected_kam)

        selected_departamento = st.sidebar.multiselect(
            "Departamento",
            self.filter_service.get_options(df_kam, "nbr_departamento"),
            key="departamento"
        )
        df_departamento = self.filter_service.filter_by_values(
            df_kam, "nbr_departamento", selected_departamento
        )

        selected_provincia = st.sidebar.multiselect(
            "Provincia",
            self.filter_service.get_options(df_departamento, "nbr_provincia"),
            key="provincia"
        )
        df_provincia = self.filter_service.filter_by_values(
            df_departamento, "nbr_provincia", selected_provincia
        )

        selected_grupo = st.sidebar.multiselect(
            "Grupo económico",
            self.filter_service.get_options(df_provincia, "grupo_economico"),
            key="grupo_economico"
        )
        df_grupo = self.filter_service.filter_by_values(
            df_provincia, "grupo_economico", selected_grupo
        )

        selected_distrito = st.sidebar.multiselect(
            "Distrito",
            self.filter_service.get_options(df_grupo, "nbr_distrito"),
            key="distrito"
        )
        df_distrito = self.filter_service.filter_by_values(
            df_grupo, "nbr_distrito", selected_distrito
        )

        has_filters = bool(
            selected_kam
            or selected_departamento
            or selected_provincia
            or selected_grupo
            or selected_distrito
        )

        if has_filters:
            st.sidebar.divider()
            st.sidebar.subheader("Direcciones")
            st.sidebar.caption("Marca una o varias direcciones. Cada una muestra el grupo económico al que pertenece.")

            selected_address_keys = self.ui_service.address_checkboxes(
                df_distrito,
                address_col="nbr_direccion",
                group_col="grupo_economico",
                id_col="sk_comercio"
            )
        else:
            selected_address_keys = []

        df_final = self.filter_service.filter_by_address_keys(
            df_distrito,
            selected_address_keys,
            address_col="nbr_direccion",
            id_col="sk_comercio"
        )

        if "sk_comercio" in df_final.columns:
            df_final = df_final.drop(columns=["sk_comercio"])

        st.subheader("Resultado filtrado")

        cols_show = [
            "kam",
            "grupo_economico",
            "num_documento",
            "nbr_departamento",
            "nbr_provincia",
            "nbr_distrito",
            "nbr_direccion",        
            "avg_gpv_ext_3m",
            "avg_ntrx_ext_3m"
        ]
        cols_show = [c for c in cols_show if c in df_final.columns]
        st.dataframe(df_final[cols_show], use_container_width=True, height=420)

        st.subheader("Mapa de puntos seleccionados")
        self.map_service.show_points_map(
            df_final,
            lat_col="num_latitud",
            lon_col="num_longitud"
        )

        if not df_final.empty and has_filters:
            if st.button("Generar rutas", key="generate_routes"):
                route_df, route_order = self.map_service.generate_route(df_final, lat_col="num_latitud", lon_col="num_longitud")
                if 'rank' not in route_df.columns:
                    st.error("No se pudo generar el ranking de ruta.")
                else:
                    st.success("Ruta generada y guardada exitosamente.")
                    st.subheader("Ranking de visita")
                    st.dataframe(route_df[["rank", "nbr_direccion", "num_latitud", "num_longitud"]], use_container_width=True)
                    st.subheader("Mapa con rutas")
                    self.map_service.show_route_map(route_df, lat_col="num_latitud", lon_col="num_longitud")

        # Sección para ver rutas guardadas
        st.divider()
        st.subheader("Rutas guardadas")
        saved_routes = self.map_service.list_saved_routes()
        if saved_routes:
            selected_route = st.selectbox("Seleccionar ruta guardada", saved_routes, key="saved_route")
            if selected_route:
                loaded_route = self.map_service.load_route(selected_route)
                if not loaded_route.empty:
                    # Mostrar información de la ruta
                    route_info = loaded_route.iloc[0] if len(loaded_route) > 0 else {}
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Puntos en ruta", len(loaded_route))
                    if 'kam' in route_info:
                        col2.metric("KAM", str(route_info['kam']))
                    if 'fecha_generacion' in route_info:
                        col3.metric("Fecha", str(route_info['fecha_generacion'])[:19])

                    st.dataframe(loaded_route, use_container_width=True)
                    if st.button("Mostrar mapa de ruta guardada", key="show_saved_route"):
                        self.map_service.show_route_map(loaded_route, lat_col="num_latitud", lon_col="num_longitud")
                else:
                    st.error("No se pudo cargar la ruta seleccionada.")
        else:
            st.info("No hay rutas guardadas aún.")

        # Opción para descargar rutas
        if saved_routes:
            st.subheader("Descargar rutas")
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_download = st.selectbox("Seleccionar ruta para descargar", saved_routes, key="download_select")
            with col2:
                if selected_download:
                    route_df = self.map_service.load_route(selected_download)
                    if not route_df.empty:
                        csv_data = route_df.to_csv(index=False)
                        st.download_button(
                            label="Descargar CSV",
                            data=csv_data,
                            file_name=f"{selected_download}.csv",
                            mime="text/csv",
                            key="download_button"
                        )

            # Descargar archivo consolidado completo
            if self.map_service.consolidated_file.exists():
                with open(self.map_service.consolidated_file, "rb") as f:
                    st.download_button(
                        label="📊 Descargar archivo consolidado completo (Excel)",
                        data=f,
                        file_name="rutas_consolidadas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_consolidated"
                    )

        # Estadísticas consolidadas
        if saved_routes:
            st.subheader("📈 Estadísticas consolidadas")

            # Leer archivo consolidado para estadísticas
            if self.map_service.consolidated_file.exists():
                try:
                    consolidated_df = pd.read_excel(self.map_service.consolidated_file, engine='openpyxl')

                    total_routes = consolidated_df['route_id'].nunique()
                    total_points = len(consolidated_df)
                    avg_points_per_route = total_points / total_routes if total_routes > 0 else 0

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total rutas generadas", total_routes)
                    col2.metric("Total puntos en rutas", total_points)
                    col3.metric("Promedio puntos por ruta", f"{avg_points_per_route:.1f}")

                    # Estadísticas por ruta para cada KAM
                    if 'kam' in consolidated_df.columns:
                        ruta_stats = []
                        for route_id in consolidated_df['route_id'].unique():
                            route_data = consolidated_df[consolidated_df['route_id'] == route_id]
                            if route_data.empty:
                                continue

                            stats = self.map_service.calculate_route_stats(route_data)
                            first_row = route_data.iloc[0]
                            ruta_stats.append({
                                'route_id': route_id,
                                'KAM': first_row.get('kam', ''),
                                'Puntos': len(route_data),
                                'Distancia estimada (km)': stats['distancia_km'],
                                'Tiempo estimado (h)': stats['tiempo_estimado_horas'],
                                'Tiempo estimado (min)': stats['tiempo_estimado_minutos'],
                                'Fecha generación': str(first_row.get('fecha_generacion', ''))[:19]
                            })

                        ruta_stats_df = pd.DataFrame(ruta_stats)
                        ruta_stats_df = ruta_stats_df.sort_values(['KAM', 'route_id'])

                        st.subheader("📊 Rutas por KAM")
                        st.dataframe(ruta_stats_df, use_container_width=True)

                        csv_kam = ruta_stats_df.to_csv(index=False)
                        st.download_button(
                            label="📊 Descargar resumen detallado por ruta",
                            data=csv_kam,
                            file_name="resumen_rutas_por_kam.csv",
                            mime="text/csv",
                            key="download_kam_summary"
                        )

                except Exception as e:
                    st.error(f"Error cargando estadísticas: {e}")

        # Gestión de rutas
        if saved_routes:
            st.subheader("🗂️ Gestión de rutas")
            st.warning("⚠️ Las eliminaciones son permanentes. El archivo consolidado se modificará.")

            # Eliminar ruta específica
            selected_to_delete = st.selectbox(
                "Seleccionar ruta para eliminar",
                ["Ninguna"] + saved_routes,
                key="delete_select"
            )

            if selected_to_delete != "Ninguna":
                # Mostrar información de la ruta a eliminar
                route_df = self.map_service.load_route(selected_to_delete)
                if not route_df.empty:
                    st.info(f"Esta ruta tiene {len(route_df)} puntos.")
                    if 'kam' in route_df.columns:
                        st.info(f"KAM: {route_df['kam'].iloc[0]}")

                    if st.button(f"🗑️ Eliminar ruta '{selected_to_delete}'", key="delete_route"):
                        try:
                            # Leer archivo consolidado
                            if self.map_service.consolidated_file.exists():
                                consolidated_df = pd.read_excel(self.map_service.consolidated_file, engine='openpyxl')

                                # Usar el route_id exacto de la ruta seleccionada
                                route_id_to_delete = str(selected_to_delete).strip()
                                if route_id_to_delete not in consolidated_df['route_id'].astype(str).values:
                                    route_id_to_delete = route_id_to_delete.split('_')[-1]

                                filtered_df = consolidated_df[consolidated_df['route_id'].astype(str) != route_id_to_delete]

                                # Guardar archivo actualizado
                                with pd.ExcelWriter(self.map_service.consolidated_file, engine='openpyxl') as writer:
                                    filtered_df.to_excel(writer, sheet_name='Rutas', index=False)

                                st.success(f"Ruta '{selected_to_delete}' eliminada exitosamente.")
                                st.rerun()
                            else:
                                st.error("Archivo consolidado no encontrado.")
                        except Exception as e:
                            st.error(f"Error eliminando ruta: {e}")
                else:
                    st.error(f"No se pudo cargar la ruta '{selected_to_delete}' para eliminar.")
                    st.info("Verifique que el archivo consolidado existe y contiene rutas.")


if __name__ == "__main__":
    app = ComercioGeoApp()
    app.run()