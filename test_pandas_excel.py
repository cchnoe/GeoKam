import pandas as pd
import numpy as np

# Crear un DataFrame de prueba
data = {
    'route_id': ['test_001'],
    'direccion': ['Test Address'],
    'latitud': [-12.0464],
    'longitud': [-77.0428],
    'kam': ['Test KAM']
}

df = pd.DataFrame(data)

# Intentar guardar como Excel
try:
    df.to_excel('test_excel.xlsx', engine='openpyxl', index=False)
    print('Excel file created successfully!')
except Exception as e:
    print(f'Error: {e}')

# Intentar leer el archivo
try:
    df_read = pd.read_excel('test_excel.xlsx', engine='openpyxl')
    print('Excel file read successfully!')
    print(df_read.head())
except Exception as e:
    print(f'Error reading: {e}')