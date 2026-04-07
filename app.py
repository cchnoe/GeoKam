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
                st.subheader("Ranking de visita")
                st.dataframe(route_df[["rank", "nbr_direccion", "num_latitud", "num_longitud"]], use_container_width=True)
                st.subheader("Mapa con rutas")
                self.map_service.show_route_map(route_df, lat_col="num_latitud", lon_col="num_longitud")


if __name__ == "__main__":
    app = ComercioGeoApp()
    app.run()