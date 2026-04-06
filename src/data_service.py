import streamlit as st
import pandas as pd
from pathlib import Path


# Función cacheada a nivel de módulo (no recibe 'self')
@st.cache_data
def _read_csv_cached(csv_path_str: str) -> pd.DataFrame:
    return pd.read_csv(csv_path_str)


class DataService:
    def load_data(self) -> pd.DataFrame:
        try:
            # Construir la ruta relativa al archivo actual (src/)
            base_dir = Path(__file__).resolve().parent
            csv_path = (base_dir.parent / "data" / "master_base.csv").resolve()
            if not csv_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado en: {csv_path}")
            df = _read_csv_cached(str(csv_path))
            return self.standardize_columns(df)
        except Exception as e:
            st.error(f"Error cargando el archivo: {e}")
            return pd.DataFrame()

    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()  

        text_cols = [
            "sk_direccion",
            "sk_comercio",
            "num_documento",
            "grupo_economico",
            "kam",
            "nbr_departamento",
            "nbr_provincia",
            "nbr_distrito",
            "nbr_direccion",
        ]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        num_cols = [
            "mes_antiguedad",
            "avg_gpv_ext_3m",
            "avg_ntrx_ext_3m",
            "num_latitud",
            "num_longitud",
        ]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df