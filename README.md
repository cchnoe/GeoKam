# Geokam — Demo Streamlit

Pequeña app de ejemplo para probar despliegue en Streamlit.

Instrucciones rápidas:

1. Crear un entorno virtual (opcional):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows PowerShell
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar la app:

```bash
streamlit run app.py
```

Uso:
- Marca "Usar datos de ejemplo" o sube un CSV con columnas `lat` y `lon`.
- Si el CSV tiene una columna `value`, verás un gráfico de ejemplo.
