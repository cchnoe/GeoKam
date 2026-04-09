# Geokam — Sistema Consolidado de Rutas

Sistema web para generación y gestión de rutas optimizadas para KAMs (Key Account Managers).

## 🚀 Características principales

### **Sistema Consolidado de Rutas**
- **Un solo archivo Excel** (`routes/rutas_consolidadas.xlsx`) para todas las rutas
- **Múltiples KAMs** pueden generar rutas simultáneamente sin conflictos
- **Thread-safe**: Manejo seguro de concurrencia entre usuarios
- **Historial completo**: Todas las rutas quedan registradas con fecha y KAM

### **Generación de Rutas Optimizadas**
- Algoritmo de **vecino más cercano** para minimizar distancia recorrida
- **Ranking automático** de visita (1, 2, 3...)
- **Mapa interactivo** con puntos conectados por líneas
- **Límites dinámicos** según selección geográfica

### **Gestión Completa**
- **Visualización** de rutas guardadas
- **Descargas individuales** (CSV por ruta)
- **Descarga consolidada** (Excel completo)
- **Estadísticas por KAM**
- **Filtros jerárquicos** (KAM → Departamento → Provincia → Grupo → Distrito)

## 📊 Estructura del Archivo Consolidado

```excel
| route_id | rank | kam | nbr_direccion | grupo_economico | num_latitud | num_longitud | fecha_generacion |
|----------|------|-----|---------------|-----------------|-------------|--------------|------------------|
| 20241201_143022 | 1 | KAM001 | Dirección 1 | Grupo A | -12.0464 | -77.0428 | 2024-12-01 14:30:22 |
| 20241201_143022 | 2 | KAM001 | Dirección 2 | Grupo B | -12.0564 | -77.0528 | 2024-12-01 14:30:22 |
```

## 🛠️ Instalación y Uso

### **Requisitos**
```bash
pip install -r requirements.txt
```

### **Ejecución**
```bash
streamlit run app.py
```

### **Acceso Multi-KAM**
1. **Comparte el enlace** de la aplicación web
2. **Cada KAM** accede desde su dispositivo
3. **Generan rutas** independientemente
4. **Todas se guardan** en el mismo archivo consolidado

## 📁 Estructura de Archivos

```
geokam/
├── app.py                    # Aplicación principal
├── requirements.txt          # Dependencias
├── src/
│   ├── data_service.py       # Carga de datos
│   ├── filter_service.py     # Filtros jerárquicos
│   ├── map_service.py        # Mapas y rutas
│   └── ui_service.py         # Componentes UI
└── routes/
    └── rutas_consolidadas.xlsx  # 🆕 Archivo consolidado
```

## 🎯 Beneficios del Sistema Consolidado

### **Para Administradores**
- **Visión global** de todas las rutas generadas
- **Estadísticas por KAM** en tiempo real
- **Descarga completa** de datos para análisis
- **Historial completo** de actividad

### **Para KAMs**
- **Interfaz intuitiva** para generar rutas
- **Mapas visuales** con orden de visita
- **Acceso desde cualquier dispositivo**
- **Trabajo independiente** sin interferencias

### **Técnicos**
- **Thread-safe** para múltiples usuarios
- **Mantenimiento sencillo** (un solo archivo)
- **Backup fácil** del archivo consolidado
- **Escalabilidad** para +27 KAMs

## 🔧 Configuración

### **Archivo de Datos**
Coloca tu archivo CSV en la carpeta `data/` con el nombre `master_base.csv`

**Columnas requeridas:**
- `kam`: Identificador del KAM
- `nbr_departamento`: Departamento
- `nbr_provincia`: Provincia
- `nbr_distrito`: Distrito
- `grupo_economico`: Grupo económico
- `nbr_direccion`: Dirección
- `num_latitud`: Latitud
- `num_longitud`: Longitud

### **Personalización**
- Modificar límites de Perú en `MapService.PERU_BOUNDS`
- Ajustar algoritmo de rutas en `generate_route()`
- Personalizar colores del mapa en `show_route_map()`

## 📈 Monitoreo y Estadísticas

- **Total de rutas** generadas
- **Puntos totales** en todas las rutas
- **Rutas por KAM** con ranking
- **Promedio de puntos** por ruta
- **Fechas de generación** de cada ruta

## 🔒 Seguridad y Concurrencia

- **Thread-safe** con bloqueos para escritura
- **Manejo de errores** robusto
- **Fallback** a archivos individuales si falla consolidado
- **Backup automático** del archivo Excel

---

**Desarrollado para optimizar la gestión territorial de KAMs con un sistema consolidado y escalable.**