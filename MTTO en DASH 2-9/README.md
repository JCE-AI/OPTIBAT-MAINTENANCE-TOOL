# OPTIBAT Maintenance Tool - Dash Version

## 📊 Descripción

Esta es la versión **Dash** equivalente de la aplicación `monthly_report_app.py` originalmente desarrollada en **Streamlit**. Mantiene toda la funcionalidad principal pero utiliza el framework Dash de Plotly para la interfaz web.

## 🚀 Características Principales

### ✅ Funcionalidades Equivalentes
- **Sistema de autenticación** con usuarios predefinidos
- **Carga de archivos** STATISTICS (.txt) múltiples
- **Detección automática de cliente** basada en flags
- **Análisis de flags principales** (7 flags monitoreados)
- **Dashboards interactivos** con KPIs
- **Visualizaciones avanzadas** con Plotly
- **Mapeo inteligente de columnas** por cliente

### 📈 Gráficos Implementados
1. **Timeline del Sistema** - Visualización temporal de todos los flags
2. **Evolución OPTIBAT_READY** - Porcentaje diario de tiempo en Ready=1
3. **Evolución Lazo Cerrado** - Porcentaje diario de tiempo en ON=1
4. **Tabla de datos** interactiva con paginación

### 🔧 Mejoras en Dash vs Streamlit

#### **Ventajas de Dash:**
- ✅ **Callbacks más eficientes** - Actualizaciones reactivas optimizadas
- ✅ **Mejor control de estado** - Manejo de sesión más robusto
- ✅ **Layouts más flexibles** - Bootstrap Components integrados
- ✅ **Interactividad avanzada** - Callbacks multi-input/output
- ✅ **Mejor rendimiento** - Actualizaciones parciales de componentes

#### **Arquitectura Dash:**
- **Componentes modulares** separados por funcionalidad
- **Store components** para manejo de datos y sesión
- **Bootstrap theme** para diseño profesional
- **Callbacks declarativos** para lógica de aplicación

## 📁 Estructura del Proyecto

```
MTTO en DASH 2-9/
├── monthly_report_dash_app.py     # Aplicación principal Dash
├── requirements.txt               # Dependencias Python
├── EJECUTAR_OPTIBAT_DASH.bat     # Launcher automático
└── README.md                     # Esta documentación
```

## 🚀 Instalación y Ejecución

### Método 1: Launcher Automático (Recomendado)
```bash
# Doble clic en el archivo .bat o desde terminal:
EJECUTAR_OPTIBAT_DASH.bat
```

### Método 2: Manual
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python monthly_report_dash_app.py
```

### 🌐 Acceso
- **URL:** http://127.0.0.1:8082
- **Puerto:** 8082 (diferente al Streamlit para evitar conflictos)

## 🔐 Credenciales de Acceso

Las mismas credenciales que la versión Streamlit:

- **Usuario:** `Administrador` | **Contraseña:** `admin123`
- **Usuario:** `demo` | **Contraseña:** `demo123`
- **Usuario:** `optibat` | **Contraseña:** `optibat2024`

## 📊 Uso de la Aplicación

### 1. **Autenticación**
- Ingresa credenciales válidas en la página de login

### 2. **Carga de Datos**
- **Sidebar izquierdo:** Arrastra archivos STATISTICS (.txt)
- **Formatos soportados:** TXT, TSV, CSV con separadores automáticos
- **Carga múltiple:** Selecciona varios archivos simultáneamente

### 3. **Análisis Automático**
- **Detección de cliente:** Basada en flags presentes
- **Mapeo de columnas:** Adaptación automática por cliente
- **KPIs calculados:** Flags activos, registros totales

### 4. **Visualizaciones**
- **Timeline del Sistema:** Todos los flags en tiempo real
- **Gráficos evolutivos:** Tendencias diarias de Ready y ON
- **Tabla interactiva:** Exploración de datos con paginación

## 🔧 Diferencias Técnicas vs Streamlit

### **Manejo de Estado**
```python
# Streamlit (session_state)
st.session_state['data'] = df

# Dash (dcc.Store)
dcc.Store(id='data-store', storage_type='session')
```

### **Callbacks vs Reactive**
```python
# Streamlit (secuencial)
if st.button("Procesar"):
    resultado = procesar_datos()
    st.write(resultado)

# Dash (callbacks declarativos)
@app.callback(Output('resultado', 'children'), Input('boton', 'n_clicks'))
def procesar(n_clicks):
    return procesar_datos()
```

### **Layouts**
```python
# Streamlit (procedural)
st.columns([1, 2, 1])
st.plotly_chart(fig)

# Dash (declarativo)
dbc.Row([dbc.Col(width=4), dbc.Col(width=8)])
dcc.Graph(figure=fig)
```

## 📈 Funcionalidades Avanzadas

### **Sistema de Flags Inteligente**
- **Mapeo automático:** Detección de variaciones por cliente
- **Fallbacks:** Funcionamiento con nombres de columna diferentes
- **Validación:** Verificación de datos antes de análisis

### **Procesamiento de Archivos**
- **Encoding robusto:** UTF-8 con fallback a latin1
- **Separadores automáticos:** Detección de tabs, comas, puntos y comas
- **Limpieza de datos:** Normalización automática de columnas

### **Visualizaciones Interactivas**
- **Hover templates:** Información detallada al pasar mouse
- **Zoom y pan:** Exploración interactiva de gráficos
- **Colores dinámicos:** Paleta expandida para múltiples flags

## ⚙️ Configuración

### **Clientes Soportados**
La aplicación lee automáticamente desde:
```
../STATISTICS FLAGS/INFORME_FLAGS_CLIENTES-tomardeaqui.xlsx
```

### **Flags Principales Monitoreados**
1. `OPTIBAT_ON` - Sistema principal activo
2. `Flag_Ready` - Sistema listo para operación
3. `Communication_ECS` - Comunicación con ECS
4. `Support_Flag_Copy` - Flag de soporte
5. `Macrostates_Flag_Copy` - Estados macro del sistema
6. `Resultexistance_Flag_Copy` - Existencia de resultados
7. `OPTIBAT_WATCHDOG` - Monitor de sistema

## 🐛 Troubleshooting

### **Puerto en Uso**
Si el puerto 8082 está ocupado:
```python
# Cambiar en monthly_report_dash_app.py línea final:
app.run_server(debug=True, host='127.0.0.1', port=8083)  # Nuevo puerto
```

### **Dependencias Faltantes**
```bash
# Instalar manualmente si hay errores:
pip install dash dash-bootstrap-components plotly pandas numpy
```

### **Archivos No Detectados**
- Verificar que los archivos sean .txt con formato STATISTICS
- Comprobar encoding (debe ser UTF-8 o latin1)
- Validar estructura con columnas Date y flags

## 📞 Soporte

**Desarrollado por:** Juan Cruz Erreguerena  
**Empresa:** Optimitive | AI Optimization Solutions  
**Versión:** Dash v1.0.0  
**Basado en:** monthly_report_app.py (Streamlit)

---

## 🎯 Conclusión

Esta versión Dash mantiene **100% de la funcionalidad** de la aplicación Streamlit original pero con **mejor rendimiento**, **mayor flexibilidad** y **callbacks más eficientes**. Es ideal para entornos de producción que requieren mayor control sobre la interfaz y el flujo de datos.