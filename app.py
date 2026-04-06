import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Geokam Demo", layout="wide")
st.title("Geokam — App de prueba para Streamlit")

st.markdown("Sube un CSV con columnas de `lat` y `lon`, o usa los datos de ejemplo.")

use_sample = st.sidebar.checkbox("Usar datos de ejemplo", value=True)
uploaded_file = st.sidebar.file_uploader("Sube un archivo CSV", type=["csv"]) if not use_sample else None

if use_sample:
	np.random.seed(42)
	df = pd.DataFrame({
		"lat": 40.4168 + np.random.randn(200) / 100,
		"lon": -3.7038 + np.random.randn(200) / 100,
		"value": np.random.randint(0, 100, 200),
	})
else:
	if uploaded_file is not None:
		try:
			df = pd.read_csv(uploaded_file)
		except Exception as e:
			st.error(f"Error leyendo el CSV: {e}")
			st.stop()
	else:
		st.info("No hay archivo subido. Marca 'Usar datos de ejemplo' o sube un CSV.")
		st.stop()

st.subheader("Vista de datos")
st.dataframe(df.head(100))

if {"lat", "lon"}.issubset(df.columns):
	st.subheader("Mapa")
	# st.map espera columnas lat/lon
	st.map(df.rename(columns={"lat": "lat", "lon": "lon"})[["lat", "lon"]])
else:
	st.warning("El DataFrame no contiene columnas 'lat' y 'lon'.")

if "value" in df.columns:
	st.subheader("Gráfico de ejemplo")
	st.line_chart(df["value"].reset_index(drop=True))

st.sidebar.markdown("---")
st.sidebar.write("Instrucciones:")
st.sidebar.write("1. Para probar localmente: `pip install -r requirements.txt`\n2. Ejecuta: `streamlit run app.py`")
