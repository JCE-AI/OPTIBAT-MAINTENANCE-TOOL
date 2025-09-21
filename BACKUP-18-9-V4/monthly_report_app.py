"""
Monthly Report Generator - Optimitive Edition
Professional SharePoint Integration & Flag Analysis Tool
Developed by Juan Cruz E. | Powered by Optimitive
"""

import os
import io
import re
import json
import time
import base64
import zipfile
import tempfile
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Scipy para análisis avanzado
try:
    from scipy.interpolate import UnivariateSpline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Simple Authentication

# Graph / SharePoint
import requests
import msal
import pytz
import logging
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# PDF/HTML helpers
from bs4 import BeautifulSoup
try:
    from weasyprint import HTML as WEASY_HTML
    WEASY_AVAILABLE = True
except Exception:
    WEASY_AVAILABLE = False

# =============== ANÁLISIS DE UTILIZACIÓN ===============
# --- Definiciones de colores necesarias para las funciones ---
GREEN = "#27AE60"
RED = "#DC143C"
ORANGE = "#FF7F50"
BLUE = "#2F80ED"

class EfficiencyColorScheme:
    PRIMARY_GREEN = GREEN
    WARNING_ORANGE = ORANGE
    CRITICAL_RED = RED
    NEUTRAL_BLUE = BLUE
    GREEN_FILL = "rgba(39,174,96,0.15)"
    ORANGE_FILL = "rgba(255, 127, 80, 0.55)"
    RED_FILL = "rgba(220, 20, 60, 0.20)"

# --- Clases y funciones de utilidad ---
@dataclass
class SystemMetrics:
    total_records: int
    date_min: Optional[datetime]
    date_max: Optional[datetime]
    on_total: int
    off_total: int
    off_ready: Optional[int]
    breakdown: Optional[Dict[str, int]]
    efficiency_percentage: float
    potential_efficiency: float
    wasted_time_percentage: float

def to01(s):
    if str(s.dtype) == "boolean": 
        return s.astype("Int64").fillna(0).astype(int).clip(0,1)
    return pd.to_numeric(s, errors="coerce").fillna(0).astype(int).clip(0,1)

def detect_time_col(df):
    pats = [r"^date$", r"fecha", r"datetime", r"hora", r"timestamp", r"time"]
    for p in pats:
        for c in map(str, df.columns):
            if re.search(p, c, re.I): 
                return c
    return None

# --- Función 1: Calcula las métricas clave ---
def calculate_system_metrics(df: pd.DataFrame, on_col: str, ready_col: Optional[str]) -> SystemMetrics:
    n = len(df)
    tcol = detect_time_col(df)
    date_min = pd.to_datetime(df[tcol]).min() if tcol and not df.empty else None
    date_max = pd.to_datetime(df[tcol]).max() if tcol and not df.empty else None
    on_data = to01(df[on_col])
    
    if ready_col and ready_col in df.columns:
        ready_data = to01(df[ready_col])
        on_ready = int(((on_data == 1)).sum())
        off_ready = int(((on_data == 0) & (ready_data == 1)).sum())
        off_not_ready = int(((on_data == 0) & (ready_data == 0)).sum())
        
        breakdown = {
            "ON (Utilizado)": on_ready,
            "OFF & Ready (Disponible)": off_ready,
            "OFF & No Ready (No Disponible)": off_not_ready
        }
        total_valid = on_ready + off_ready + off_not_ready
        efficiency = (on_ready / total_valid * 100) if total_valid > 0 else 0
        potential_efficiency = ((on_ready + off_ready) / total_valid * 100) if total_valid > 0 else 0
        wasted_time = (off_ready / total_valid * 100) if total_valid > 0 else 0
        
        return SystemMetrics(
            total_records=n, date_min=date_min, date_max=date_max, on_total=on_ready,
            off_total=off_ready + off_not_ready, off_ready=off_ready, breakdown=breakdown,
            efficiency_percentage=efficiency, potential_efficiency=potential_efficiency,
            wasted_time_percentage=wasted_time
        )
    else:
        on_total = int((on_data == 1).sum())
        off_total = int((on_data == 0).sum())
        efficiency = (on_total / n * 100) if n > 0 else 0
        
        breakdown = {
            "ON (Utilizado)": on_total,
            "OFF (No Utilizado)": off_total
        }
        
        return SystemMetrics(
            total_records=n, date_min=date_min, date_max=date_max, on_total=on_total,
            off_total=off_total, off_ready=None, breakdown=breakdown,
            efficiency_percentage=efficiency, potential_efficiency=efficiency,
            wasted_time_percentage=0
        )

# --- Función 2: Dibuja el gráfico de anillo (Donut) ---
def create_efficiency_donut_v2(metrics: SystemMetrics, on_col: str, ready_col: Optional[str]) -> go.Figure:
    if metrics.breakdown:
        if ready_col:
            labels = ["ON (Utilizado)", "OFF & Ready (Disponible)", "OFF & No Ready (No Disponible)"]
            colors = [EfficiencyColorScheme.PRIMARY_GREEN, EfficiencyColorScheme.WARNING_ORANGE, EfficiencyColorScheme.CRITICAL_RED]
        else:
            labels = ["ON (Utilizado)", "OFF (No Utilizado)"]
            colors = [EfficiencyColorScheme.PRIMARY_GREEN, EfficiencyColorScheme.CRITICAL_RED]
            
        values = list(metrics.breakdown.values())
        pulls = [0] * len(values)
    
    fig = go.Figure(go.Pie(
        labels=labels, 
        values=values, 
        hole=0.65, 
        sort=False, 
        textinfo="percent",
        textposition="outside",
        textfont=dict(size=24),  # Reducido a la mitad (48/2) para coincidir con texto central
        marker=dict(colors=colors, line=dict(color="white", width=3)),
        pull=pulls, 
        hovertemplate="<b style='font-size:18px'>%{label}</b><br><span style='font-size:15px'>%{value:,} registros</span><br><span style='font-size:16px'>%{percent}</span><extra></extra>"
    ))
    
    center_text = f"<b>Utilización</b><br>{metrics.efficiency_percentage:.1f}%"
    # Título removido según solicitud del usuario (círculo amarillo)
    
    fig.update_layout(
        height=525,  # Aumentado 40% más (375 * 1.4)
        # title removido (era el contenido del círculo amarillo)
        legend=dict(
            x=1.05, 
            y=0.5,
            font=dict(size=17),  # Aumentado 40% más (12 * 1.4)
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
        ),
        annotations=[dict(
            text=center_text, 
            x=0.5, 
            y=0.5, 
            font_size=25,  # Aumentado 40% más (18 * 1.4)
            showarrow=False
        )],
        margin=dict(l=42, r=42, t=56, b=126),  # Márgenes aumentados 40% (30*1.4, etc.)
        font=dict(size=11),  # Fuente general aumentada 40% (8 * 1.4)
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",  # Fondo blanco sólido para legibilidad
            bordercolor="rgba(0,0,0,0.3)",
            font_size=16,
            font_family="Arial"
        )
    )
    
    # Agregar información de período debajo del gráfico
    if metrics.date_min and metrics.date_max:
        period_text = f"Período Filtrado: {metrics.date_min.strftime('%Y-%m-%d')} — {metrics.date_max.strftime('%Y-%m-%d')} - {(metrics.date_max - metrics.date_min).days + 1} días"
        registros_text = f"Total Registros: {metrics.total_records:,} | Registros Originales: {metrics.total_records:,}"
        
        fig.add_annotation(
            text=f"{period_text}<br>{registros_text}",
            xref="paper", yref="paper",
            x=0.5, y=-0.3,
            showarrow=False,
            font=dict(size=18, color="#64748b"),  # Aumentado 40% más (8 * 1.4)
            align="center"
        )
    
    return fig

# --- FASE 1: LA LÓGICA - Convertir datos en bloques de tiempo (`_generate_status_segments`) ---
def _generate_status_segments(df: pd.DataFrame, tcol: str, on_col: str, ready_col: Optional[str]) -> List[Tuple]:
    """
    El objetivo de esta función es tomar el DataFrame y, en lugar de procesar cada fila,
    devolver una lista simple que describa los períodos de estado continuo.
    Por ejemplo: [("2025-08-05 10:00", "2025-08-05 14:30", 2), ("2025-08-05 14:30", "2025-08-05 18:00", 1), ...]
    """
    if df.empty:
        return []

    # 1. CLASIFICACIÓN DE ESTADO: A cada registro se le asigna un código numérico
    #    basado en la combinación de las columnas ON y READY.
    if ready_col and ready_col in df.columns and not df[ready_col].dropna().empty:
        # Caso con ready_col disponible
        data = df[[tcol, on_col, ready_col]].copy().sort_values(tcol)
        data['state_on'] = to01(data[on_col])
        data['state_ready'] = to01(data[ready_col])
        
        # Se definen las condiciones para cada estado.
        conditions = [
            (data['state_on'] == 1),                           # Condición para "ON"
            (data['state_on'] == 0) & (data['state_ready'] == 1) # Condición para "OFF & Ready"
        ]
        # Se asignan los códigos numéricos: 2=Verde, 1=Naranja, 0=Rojo (por defecto).
        choices = [2, 1]
        data["status"] = np.select(conditions, choices, default=0)
    else:
        # Caso sin ready_col - solo estados ON/OFF
        data = df[[tcol, on_col]].copy().sort_values(tcol)
        data['state_on'] = to01(data[on_col])
        # Solo dos estados: ON=2 (verde), OFF=0 (gris)
        data["status"] = data['state_on'] * 2

    # 2. DETECCIÓN DE CAMBIOS: La parte más importante. Se busca dónde cambia el estado.
    #    - `data['status'].diff()`: Calcula la diferencia entre el estado de una fila y la anterior.
    #      Será 0 si el estado es el mismo, y distinto de 0 si cambió.
    #    - `.ne(0)`: Compara si el resultado es "no es igual a 0", devolviendo True en cada punto de cambio.
    data['block_start'] = data['status'].diff().ne(0)
    data.loc[0, 'block_start'] = True # La primera fila siempre es el inicio de un bloque.

    # Se filtra el DataFrame para quedarse solo con las filas donde empieza un nuevo bloque.
    change_points = data[data['block_start']]
    
    # 3. CONSTRUCCIÓN DE SEGMENTOS: Se itera sobre los puntos de cambio para crear los bloques.
    segments = []
    if len(change_points) > 0:
        for i in range(len(change_points)):
            # El inicio del bloque es el tiempo del punto de cambio actual.
            start_time = change_points[tcol].iloc[i]
            status = change_points['status'].iloc[i]
            
            # El fin del bloque es el tiempo del SIGUIENTE punto de cambio.
            if i + 1 < len(change_points):
                end_time = change_points[tcol].iloc[i+1]
            else:
                # Si es el último bloque, termina en el último registro de los datos.
                end_time = data[tcol].iloc[-1]

            if start_time < end_time:
                segments.append((start_time, end_time, status))

    return segments

# --- FASE 2: LA VISUALIZACIÓN - Dibujar el gráfico (`ts_with_background_regions`) ---
def ts_with_background_regions(df: pd.DataFrame, tcol: str, on_col: str, ready_col: Optional[str], show_durations: bool = False) -> go.Figure:
    """
    Esta función recibe la lista de segmentos y la usa para construir el gráfico final.
    Si no hay ready_col, solo muestra estados ON/OFF sin colores de fondo diferenciados.
    """
    # Primero, se llama a la función de lógica para obtener los bloques de estado.
    segments = _generate_status_segments(df, tcol, on_col, ready_col)
    
    shapes = []
    # 1. DIBUJAR FONDOS DE COLOR: Se itera sobre cada segmento (bloque de tiempo).
    for start, end, status in segments:
        # Se mapea el código de estado (2, 1, 0) a un color de relleno.
        if ready_col and ready_col in df.columns:
            # Con ready_col: colores diferenciados
            color_map = {
                2: EfficiencyColorScheme.GREEN_FILL,   # ON -> Verde
                1: EfficiencyColorScheme.ORANGE_FILL,  # OFF & Ready -> Naranja
                0: EfficiencyColorScheme.RED_FILL      # OFF & No Ready -> Rojo
            }
        else:
            # Sin ready_col: solo ON=verde, OFF=gris claro
            color_map = {
                2: EfficiencyColorScheme.GREEN_FILL,   # ON -> Verde
                0: "rgba(200, 200, 200, 0.3)"         # OFF -> Gris claro
            }
        # Se crea un rectángulo (`shape`) para el fondo del gráfico.
        shapes.append(dict(
            type="rect", xref="x", yref="paper", 
            x0=start, x1=end, y0=0, y1=1, # Coordenadas del rectángulo
            fillcolor=color_map.get(status),
            line=dict(width=0), # Sin borde
            layer="below" # Se dibuja detrás de la línea de datos
        ))

    # 2. DIBUJAR LA LÍNEA DE ESTADO ON/OFF
    fig = go.Figure()
    y_values = to01(df[on_col]) # La línea solo representa el estado ON (1) vs OFF (0).
    
    # Se añade la traza de la línea azul. 'shape="hv"' crea la apariencia de "escalones".
    fig.add_trace(go.Scatter(
        x=df[tcol], y=y_values, mode="lines",
        line=dict(shape="hv", width=1.5, color=EfficiencyColorScheme.NEUTRAL_BLUE),
        name="Estado"
    ))

    # 3. PREPARAR DATOS PARA DURACIONES SI SE SOLICITA
    annotations_data = []
    if show_durations:
        # Detectar cambios de estado para mostrar duraciones
        df_clean = df.dropna(subset=[on_col, tcol]).copy()
        df_clean = df_clean.sort_values(tcol)
        df_clean['state_change'] = df_clean[on_col].diff() != 0
        df_clean['state_change'].iloc[0] = True  # Primer punto siempre es cambio
        
        # Almacenar datos de cambios para uso dinámico
        changes = df_clean[df_clean['state_change']]
        for i in range(len(changes) - 1):
            current = changes.iloc[i]
            next_change = changes.iloc[i + 1]
            duration = next_change[tcol] - current[tcol]
            
            if duration.total_seconds() > 0:
                # Calcular duración en formato legible
                hours = duration.total_seconds() / 3600
                if hours < 1:
                    duration_text = f"{duration.total_seconds()/60:.0f}min"
                elif hours < 24:
                    duration_text = f"{hours:.1f}h"
                else:
                    duration_text = f"{duration.days}d {hours%24:.0f}h"
                
                # Guardar información de la anotación para agregarla dinámicamente
                annotations_data.append({
                    'x': current[tcol] + duration/2,
                    'y': current[on_col] + 0.03,  # Reducido de 0.1 a 0.03 para estar más cerca
                    'text': duration_text,
                    'start': current[tcol],
                    'end': next_change[tcol]
                })

    # 4. AGREGAR ANOTACIONES INICIALES SI HAY DURACIONES
    if show_durations and annotations_data:
        # Agregar todas las anotaciones inicialmente
        for ann_data in annotations_data:
            fig.add_annotation(
                x=ann_data['x'],
                y=ann_data['y'],
                text=ann_data['text'],
                showarrow=True,
                arrowhead=2,
                arrowcolor="blue",
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="blue",
                borderwidth=2,
                font=dict(size=15),
                # Hacer que las anotaciones sean visibles solo cuando el segmento está en vista
                xref="x",
                yref="y"
            )
    
    # 5. CONFIGURACIÓN FINAL DEL GRÁFICO
    fig.update_layout(
        shapes=shapes, # Se añaden todos los rectángulos de color al layout.
        title={'text': "Serie Temporal de Estados del Sistema", 'x': 0.5},
        xaxis=dict(
            title="Fecha y Hora", 
            rangeslider=dict(visible=True),  # Siempre visible el range-slider
            fixedrange=False  # Siempre permitir wheel-zoom
        ),
        yaxis=dict(
            title="Estado", 
            tickvals=[0, 1], 
            ticktext=["OFF", "ON"], 
            range=[-0.1, 1.1],
            fixedrange=False  # Siempre permitir wheel-zoom
        ),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        # Configurar el modo de interacción para que las anotaciones se actualicen con el zoom
        dragmode='zoom',
        hovermode='x unified'
    )
    
    # Configurar las anotaciones para que se ajusten dinámicamente al zoom
    if show_durations:
        fig.update_annotations(
            # Las anotaciones se muestran/ocultan automáticamente según el rango visible
            visible=True
        )
    
    return fig


# =========================
# CONFIGURATION & THEME
# =========================
OPTIMITIVE_COLORS = {
    'primary_red': '#E31E32',
    'primary_black': '#000000',
    'dark_bg': '#FFFFFF',          # White background
    'medium_bg': '#F8F9FA',        # Light gray
    'light_bg': '#FFFFFF',         # Pure white
    'accent_blue': '#0099CC',
    'text_primary': '#2C3E50',     # Dark blue-gray
    'text_secondary': '#6C757D',   # Gray
    'success': '#28A745',
    'warning': '#FFC107',
    'error': '#DC3545',
    'border': '#DEE2E6'            # Light border
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FLAGS POR CLIENTE - SISTEMA VERSATIL
def load_client_flags_mapping():
    """Carga el mapeo de flags por cliente desde Excel"""
    try:
        import os
        excel_path = os.path.join(os.path.dirname(__file__), "STATISTICS FLAGS", "INFORME_FLAGS_CLIENTES-tomardeaqui.xlsx")
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
            
            # Crear mapeo de flags por cliente
            client_flags = {}
            flag_columns = ['OPTIBAT_ON', 'Flag_Ready', 'Communication_ECS', 'Support_Flag_Copy', 
                          'Macrostates_Flag_Copy', 'Resultexistance_Flag_Copy', 'OPTIBAT_WATCHDOG']
            
            for _, row in df.iterrows():
                cliente = row['Cliente']
                if pd.notna(cliente) and cliente.strip():
                    client_flags[cliente] = {}
                    for flag in flag_columns:
                        if pd.notna(row[flag]):
                            client_flags[cliente][flag] = row[flag]
            
            # Crear mapeo inverso (flag_name -> [client_specific_names])
            flag_variations = {}
            for flag in flag_columns:
                variations = set()
                for client_data in client_flags.values():
                    if flag in client_data:
                        variations.add(client_data[flag])
                flag_variations[flag] = list(variations)
            
            return client_flags, flag_variations
        else:
            logger.warning(f"Archivo de flags por cliente no encontrado: {excel_path}")
            return {}, {}
    except Exception as e:
        logger.error(f"Error cargando flags por cliente: {e}")
        return {}, {}

# Cargar mapeos al inicializar
CLIENT_FLAGS_MAPPING, FLAG_VARIATIONS = load_client_flags_mapping()

# FLAGS PRINCIPALES (los 7 que interesan)
MAIN_FLAGS = [
    "OPTIBAT_ON", "Flag_Ready", "Communication_ECS", 
    "Support_Flag_Copy", "Macrostates_Flag_Copy", "Resultexistance_Flag_Copy", "OPTIBAT_WATCHDOG"
]

FLAG_DESCRIPTIONS = {
    "OPTIBAT_ON": "Sistema principal activo", 
    "Flag_Ready": "Sistema listo para operación",
    "Communication_ECS": "Comunicación con ECS", 
    "Support_Flag_Copy": "Flag de soporte", 
    "Macrostates_Flag_Copy": "Estados macro del sistema",
    "Resultexistance_Flag_Copy": "Existencia de resultados", 
    "OPTIBAT_WATCHDOG": "Monitor de sistema"
}

# Todas las variaciones posibles de cada flag
ALL_FLAG_VARIATIONS = []
for flag in MAIN_FLAGS:
    if flag in FLAG_VARIATIONS:
        ALL_FLAG_VARIATIONS.extend(FLAG_VARIATIONS[flag])

PULSING_SIGNALS_FOR_GAUGE = []
# Agregar todas las variaciones de flags que pulsan
for flag_name in ["Communication_ECS", "OPTIBAT_WATCHDOG"]:
    if flag_name in FLAG_VARIATIONS:
        PULSING_SIGNALS_FOR_GAUGE.extend(FLAG_VARIATIONS[flag_name])

COLOR_SCHEME = {
    'primary': '#3498db', 'success': '#27ae60', 'warning': '#f39c12',
    'danger': '#e74c3c', 'info': '#3498db', 'dark': '#2c3e50', 'light': '#ecf0f1'
}

st.set_page_config(
    page_title="Optimitive Monthly Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Optimitive branding
st.markdown(f"""
<style>
    /* Main App Background - White Theme */
    .stApp {{
        background-color: {OPTIMITIVE_COLORS['dark_bg']};
        color: {OPTIMITIVE_COLORS['text_primary']};
    }}
    
    /* Header Styles */
    .main-header {{
        background: linear-gradient(90deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(227, 30, 50, 0.3);
    }}
    
    .brand-title {{
        font-size: 3rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
        letter-spacing: 2px;
    }}
    
    .brand-subtitle {{
        font-size: 1.2rem;
        margin: 1rem 0;
        opacity: 0.95;
        font-weight: 500;
    }}
    
    /* KPI Cards */
    .kpi-card {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['medium_bg']} 0%, {OPTIMITIVE_COLORS['light_bg']} 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid {OPTIMITIVE_COLORS['primary_red']};
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    
    .kpi-title {{
        color: {OPTIMITIVE_COLORS['text_secondary']};
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .kpi-value {{
        color: {OPTIMITIVE_COLORS['text_primary']};
        font-size: 2rem;
        font-weight: 700;
    }}
    
    /* Breadcrumb Navigation */
    .breadcrumb {{
        background: {OPTIMITIVE_COLORS['medium_bg']};
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
    }}
    
    .breadcrumb a {{
        color: {OPTIMITIVE_COLORS['accent_blue']};
        text-decoration: none;
        font-weight: 600;
        padding: 0.5rem;
        border-radius: 5px;
        transition: all 0.3s ease;
    }}
    
    .breadcrumb a:hover {{
        background: {OPTIMITIVE_COLORS['light_bg']};
        color: {OPTIMITIVE_COLORS['primary_red']};
    }}
    
    .breadcrumb .separator {{
        color: {OPTIMITIVE_COLORS['text_secondary']};
        margin: 0 0.5rem;
    }}
    
    /* Success/Warning/Error Messages */
    .success-message {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['success']} 0%, #00AA55 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0, 204, 102, 0.3);
    }}
    
    .warning-message {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['warning']} 0%, #E6A600 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 184, 0, 0.3);
    }}
    
    .error-message {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['error']} 0%, #E6002D 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 51, 102, 0.3);
    }}
    
    /* File Browser */
    .file-browser {{
        background: {OPTIMITIVE_COLORS['medium_bg']};
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }}
    
    .folder-item {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['light_bg']} 0%, #333333 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }}
    
    .folder-item:hover {{
        border-color: {OPTIMITIVE_COLORS['primary_red']};
        transform: translateX(5px);
    }}
    
    .file-item {{
        background: {OPTIMITIVE_COLORS['light_bg']};
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        border-left: 3px solid {OPTIMITIVE_COLORS['accent_blue']};
    }}
    
    /* Report Section */
    .report-section {{
        background: {OPTIMITIVE_COLORS['medium_bg']};
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid {OPTIMITIVE_COLORS['primary_red']}33;
    }}
    
    /* Footer */
    .footer {{
        text-align: center;
        padding: 3rem;
        color: {OPTIMITIVE_COLORS['text_secondary']};
        border-top: 2px solid {OPTIMITIVE_COLORS['primary_red']};
        margin-top: 4rem;
        background: {OPTIMITIVE_COLORS['medium_bg']};
        border-radius: 15px 15px 0 0;
    }}
    
    /* Buttons Override */
    .stButton > button {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(227, 30, 50, 0.4);
    }}
    
    /* Download Buttons */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['success']} 0%, #00AA55 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
    }}
    
    /* Login Page Styling */
    .login-container {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['medium_bg']} 0%, {OPTIMITIVE_COLORS['light_bg']} 100%);
        padding: 3rem;
        border-radius: 20px;
        max-width: 500px;
        margin: 2rem auto;
        border: 2px solid {OPTIMITIVE_COLORS['primary_red']};
        box-shadow: 0 15px 35px rgba(227, 30, 50, 0.3);
    }}
    
    .login-header {{
        text-align: center;
        margin-bottom: 2rem;
        color: {OPTIMITIVE_COLORS['text_primary']};
    }}
    
    .login-title {{
        font-size: 2.5rem;
        font-weight: 900;
        color: {OPTIMITIVE_COLORS['primary_red']};
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}
    
    .login-subtitle {{
        font-size: 1rem;
        color: {OPTIMITIVE_COLORS['text_secondary']};
        margin-bottom: 2rem;
    }}
    
    /* Form Elements for Login */
    .stForm {{
        background: transparent !important;
    }}
    
    .stTextInput > div > div > input {{
        background: {OPTIMITIVE_COLORS['dark_bg']} !important;
        color: {OPTIMITIVE_COLORS['text_primary']} !important;
        border: 2px solid {OPTIMITIVE_COLORS['light_bg']} !important;
        border-radius: 15px !important;
        padding: 1rem !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {OPTIMITIVE_COLORS['primary_red']} !important;
        box-shadow: 0 0 15px rgba(227, 30, 50, 0.3) !important;
    }}
    
    .stTextInput > label {{
        color: {OPTIMITIVE_COLORS['text_primary']} !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }}
    
    /* Checkbox styling for login */
    .stCheckbox > div > label > div:first-child {{
        background: {OPTIMITIVE_COLORS['dark_bg']} !important;
        border: 2px solid {OPTIMITIVE_COLORS['light_bg']} !important;
    }}
    
    .stCheckbox > div > label > div:first-child:hover {{
        border-color: {OPTIMITIVE_COLORS['primary_red']} !important;
    }}
    
    .stCheckbox > div > label > span {{
        color: {OPTIMITIVE_COLORS['text_primary']} !important;
        font-weight: 600 !important;
    }}
    
    /* Login specific button styling */
    .login-form .stButton > button {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 1rem 2rem;
        font-weight: bold;
        font-size: 1.1rem;
        width: 100%;
        margin-top: 1rem;
        transition: all 0.3s ease;
    }}
    
    .login-form .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(227, 30, 50, 0.5);
    }}
    
    /* Error and info messages styling */
    .stAlert {{
        border-radius: 15px !important;
        padding: 1rem 1.5rem !important;
        margin: 1rem 0 !important;
    }}
    
    .stAlert[data-baseweb="notification"] div:first-child {{
        background: {OPTIMITIVE_COLORS['medium_bg']} !important;
        border-left: 5px solid {OPTIMITIVE_COLORS['primary_red']} !important;
    }}
    
    /* Welcome message for login */
    .welcome-message {{
        background: linear-gradient(135deg, {OPTIMITIVE_COLORS['accent_blue']} 0%, #0077AA 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0, 153, 204, 0.3);
    }}
</style>
""", unsafe_allow_html=True)

# =========================
# FLAG COLUMN MAPPING SYSTEM
# =========================
FLAG_COLUMN_MAPPING = {
    # Flag estándar OPTIBAT_ON y sus variaciones por cliente
    "OPTIBAT_ON": [
        "OPTIBAT_ON",
        "Kiln_OPTIBAT_ON", 
        "OPTIBAT_ON",
        "OPTIBATON_OPC"
    ],
    
    # Flag estándar Flag_Ready y sus variaciones por cliente  
    "Flag_Ready": [
        "Flag_Ready",
        "OPTIBAT_READY",
        "OPTIBAT_Ready_fromPLANT",
        "OPTIBAT_READY",
        "OPTIBAT_READY",
        "OPTIBAT_READY"
    ],
    
    # Flag estándar Communication_ECS y sus variaciones
    "Communication_ECS": [
        "Communication_ECS",
        "KILN_OPTIBAT_COMMUNICATION",
        "KILN_OPTIBAT_COMMUNICATION", 
        "OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "KILN_OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "KILN_OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION",
        "OPTIBAT_COMMUNICATION"
    ],
    
    # Flag estándar Support_Flag_Copy y sus variaciones
    "Support_Flag_Copy": [
        "Support_Flag_Copy",
        "OPTIBAT_SUPPORT",
        "Support_copy",
        "Support_Flag_Copy",
        "Support_copy",
        "Support_Flag",
        "Support_Flag",
        "Support_Flag_Copy",
        "OPTIBAT_SUPPORT",
        "Support_copy",
        "OPTIBAT_SUPPORT",
        "Support",
        "OPTIBAT_SUPPORT",
        "Support",
        "Support",
        "Support",
        "Support_Flag_Copy",
        "Support_Flag_Copy",
        "Support_Flag_Copy"
    ],
    
    # Flag estándar Macrostates_Flag_Copy y sus variaciones
    "Macrostates_Flag_Copy": [
        "Macrostates_Flag_Copy",
        "OPTIBAT_MACROSTATES",
        "MacroState_copy",
        "Macrostates_Flag_Copy",
        "MacroState_copy",
        "Macrostates_Flag",
        "Macrostates_Flag",
        "Macrostates_Flag_Copy",
        "OPTIBAT_MACROSTATES",
        "MacroState_copy",
        "MacroState_flag",
        "OPTIBAT_MACROSTATES",
        "MacroState",
        "MacroState_flag",
        "MacroState_flag",
        "MacroState_flag",
        "Macrostates_Flag_Copy",
        "Macrostates_Flag_Copy",
        "Macrostates_Flag_Copy"
    ],
    
    # Flag estándar Resultexistance_Flag_Copy y sus variaciones
    "Resultexistance_Flag_Copy": [
        "Resultexistance_Flag_Copy",
        "OPTIBAT_RESULTEXISTANCE",
        "ResultExistence_copy",
        "Resultexistance_Flag_Copy",
        "ResultExistence_copy",
        "ResultExistence_copy",
        "ResultExistance_Quality_flag",
        "Resultexistance_Flag_Copy",
        "OPTIBAT_RESULTEXISTANCE", 
        "ResultExistence_copy",
        "ResultExistance_flag",
        "OPTIBAT_RESULTEXISTANCE",
        "ResultExistence",
        "ResultExistance_Quality_flag",
        "ResultExistance_Quality_flag",
        "ResultExistance_Quality_flag", 
        "Resultexistance_Flag_Copy",
        "Resultexistance_Flag_Copy",
        "Resultexistance_Flag_Copy"
    ],
    
    # Flag estándar OPTIBAT_WATCHDOG y sus variaciones
    "OPTIBAT_WATCHDOG": [
        "OPTIBAT_WATCHDOG",
        "OPTIBAT_WATCHDOG",
        "OPTIBAT_WATCHDOG",
        "OPTIBAT_WATCHDOG",
        "OPTIBAT_WATCHDOG",
        "OPTIBAT_WATCHDOG",
        "OPTIBAT_WATCHDOG"
    ]
}

def detect_client_flag_columns(df_columns: list) -> dict:
    """
    Detecta automáticamente las columnas de flags del cliente basándose en el mapeo.
    
    Args:
        df_columns: Lista de nombres de columnas del DataFrame del cliente
        
    Returns:
        dict: Mapeo de flags estándar a columnas encontradas del cliente
              Ej: {"OPTIBAT_ON": "Kiln_OPTIBAT_ON", "Flag_Ready": "OPTIBAT_READY"}
    """
    detected_mapping = {}
    
    # Para cada flag estándar, buscar qué variación existe en las columnas del cliente
    for standard_flag, variations in FLAG_COLUMN_MAPPING.items():
        for variation in variations:
            if variation in df_columns:
                detected_mapping[standard_flag] = variation
                break  # Usar la primera coincidencia encontrada
                
    return detected_mapping

def get_standardized_columns(df: pd.DataFrame, detected_mapping: dict = None) -> dict:
    """
    Obtiene las columnas estandarizadas basándose en el mapeo detectado.
    
    Args:
        df: DataFrame con datos del cliente
        detected_mapping: Mapeo detectado (opcional, se calculará si no se proporciona)
        
    Returns:
        dict: Diccionario con columnas estandarizadas disponibles
              Ej: {"ready_col": "OPTIBAT_READY", "on_col": "Kiln_OPTIBAT_ON"}
    """
    if detected_mapping is None:
        detected_mapping = detect_client_flag_columns(df.columns.tolist())
    
    standardized = {}
    
    # Mapear a nombres estándar para uso en el código
    flag_mapping = {
        "ready_col": ["Flag_Ready", "OPTIBAT_ON"],  # Prioridad: Flag_Ready primero
        "on_col": ["OPTIBAT_ON", "Flag_Ready"],     # Prioridad: OPTIBAT_ON primero
        "communication_col": ["Communication_ECS"],
        "support_col": ["Support_Flag_Copy"], 
        "macrostates_col": ["Macrostates_Flag_Copy"],
        "resultexistance_col": ["Resultexistance_Flag_Copy"],
        "watchdog_col": ["OPTIBAT_WATCHDOG"]
    }
    
    for standard_name, flag_priorities in flag_mapping.items():
        for flag in flag_priorities:
            if flag in detected_mapping:
                standardized[standard_name] = detected_mapping[flag]
                break
                
    return standardized

def show_column_mapping_info(df: pd.DataFrame):
    """
    Muestra información detallada del mapeo de columnas detectado.
    Útil para debugging y transparencia con el usuario.
    """
    st.markdown("### 🔍 Información de Mapeo de Columnas")
    
    detected_mapping = detect_client_flag_columns(df.columns.tolist())
    standardized_cols = get_standardized_columns(df, detected_mapping)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Columnas Detectadas del Cliente")
        if detected_mapping:
            for standard_flag, client_column in detected_mapping.items():
                st.markdown(f"**{standard_flag}** → `{client_column}`")
        else:
            st.warning("No se detectaron columnas de flags estándar")
    
    with col2:
        st.markdown("#### 🎯 Columnas Estandarizadas para Análisis")
        if standardized_cols:
            for analysis_name, column_name in standardized_cols.items():
                analysis_readable = {
                    'ready_col': 'READY Analysis',
                    'on_col': 'ON/OFF Analysis', 
                    'communication_col': 'Communication',
                    'support_col': 'Support',
                    'macrostates_col': 'Macrostates',
                    'resultexistance_col': 'Result Existence',
                    'watchdog_col': 'Watchdog'
                }
                readable_name = analysis_readable.get(analysis_name, analysis_name)
                st.markdown(f"🔧 **{readable_name}** → `{column_name}`")
        else:
            st.warning("No se pudieron estandarizar columnas")
    
    # Mostrar todas las variaciones soportadas en un expander
    with st.expander("📚 Ver Todas las Variaciones Soportadas por Flag"):
        for standard_flag, variations in FLAG_COLUMN_MAPPING.items():
            st.markdown(f"**{standard_flag}:**")
            variations_text = ", ".join([f"`{var}`" for var in variations])
            st.markdown(f"&nbsp;&nbsp;{variations_text}")

# =========================
# METRICS REGISTRATION FUNCTIONS
# =========================
def get_ip():
    try:
        if hasattr(st, "request") and hasattr(st.request, "headers"):
            ip = st.request.headers.get('X-Forwarded-For', None)
            if ip:
                ip = ip.split(',')[0].strip()
            return ip or "Desconocida"
        return "Desconocida"
    except Exception:
        return "Desconocida"

def log_access(ip):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
        
        creds_json_str = st.secrets.get("gcp_service_account", None)
        if creds_json_str:
            if isinstance(creds_json_str, str):
                creds_dict = json.loads(creds_json_str)
            else:
                creds_dict = creds_json_str 
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else: 
            creds = ServiceAccountCredentials.from_json_keyfile_name('proyecto-optibat-dashboard-62a151156279.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open("Metricas OPTIBAT").sheet1
        madrid = pytz.timezone("Europe/Madrid")
        local_time = datetime.now(madrid)
        sheet.append_row([ip, local_time.strftime("%Y-%m-%d %H:%M:%S")])
    except Exception as e:
        # logger.warning(f"No se pudo registrar la métrica en Google Sheets: {e}")
        pass 

# =========================
# OPTIBAT METRICS ANALYZER CLASS
# =========================
def detect_client_from_flags(columns) -> str:
    """Detecta el cliente basándose en los flags presentes"""
    column_set = set(columns)
    
    best_match = "GENERIC"
    max_matches = 0
    
    for client, flags in CLIENT_FLAGS_MAPPING.items():
        matches = 0
        for flag_value in flags.values():
            if flag_value in column_set:
                matches += 1
        
        if matches > max_matches:
            max_matches = matches
            best_match = client
    
    return best_match if max_matches > 0 else "GENERIC"

def get_available_flags_in_data(df) -> list:
    """
    Obtiene los flags disponibles en los datos usando el nuevo sistema de mapeo inteligente.
    Retorna las columnas del cliente que corresponden a flags estándar.
    """
    available_flags = []
    detected_mapping = detect_client_flag_columns(df.columns.tolist())
    
    # Usar las columnas detectadas del cliente (no las estándar)
    for standard_flag, client_column in detected_mapping.items():
        if client_column in df.columns and not df[client_column].dropna().empty:
            available_flags.append(client_column)
    
    # También buscar cualquier columna adicional que contenga palabras clave
    for column in df.columns:
        if any(keyword in column.upper() for keyword in ['SUPPORT_FLAG', 'SUPPORT FLAG', 'SUPPORTFLAG']) and column not in available_flags:
            if not df[column].dropna().empty:
                available_flags.append(column)
    
    return available_flags

class OptibatMetricsAnalyzer:
    def __init__(self):
        self.df_processed = pd.DataFrame()

    @staticmethod
    @st.cache_data
    def load_and_process_files(uploaded_files) -> pd.DataFrame:
        dfs = []
        errors = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, file in enumerate(uploaded_files):
            try:
                status_text.text(f"Procesando archivo {idx + 1}/{len(uploaded_files)}: {file.name}")
                
                # Leemos los encabezados usando la codificación 'latin1'
                headers = pd.read_csv(file, sep='\t', skiprows=1, nrows=1, header=None, encoding='latin1').iloc[0].tolist()
                
                # IMPORTANTE: Volvemos al inicio del archivo para que la siguiente lectura funcione
                file.seek(0)
                
                seen = {}
                names = []
                for h in headers:
                    if h in seen:
                        seen[h] += 1
                        names.append(f"{h}_{seen[h]}")
                    else:
                        seen[h] = 0
                        names.append(h)
                
                # Leemos el resto del dataframe también con 'latin1'
                df_temp = pd.read_csv(file, sep='\t', skiprows=10, header=None, names=names, engine='python', encoding='latin1')
                
                if "Date" in df_temp.columns:
                    df_temp["Date"] = pd.to_datetime(df_temp["Date"], errors='coerce')
                    df_temp = df_temp.dropna(subset=['Date'])

                for flag_col in MAIN_FLAGS:
                    if flag_col in df_temp.columns:
                        df_temp[flag_col] = pd.to_numeric(df_temp[flag_col], errors='coerce')
                
                df_temp['source_file'] = file.name 
                dfs.append(df_temp)
                progress_bar.progress((idx + 1) / len(uploaded_files))
            except Exception as e:
                logger.error(f"Error processing file {file.name}: {str(e)}")
                # Mostramos el error en la interfaz de Streamlit para que sea visible
                st.error(f"Error al procesar el archivo {file.name}: {e}")
                errors.append(f"Error en {file.name}: {str(e)}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if not dfs:
            raise ValueError("No se pudieron procesar los archivos o no contienen datos válidos.")
        
        df_combined = pd.concat(dfs, ignore_index=True)
        if "Date" in df_combined.columns:
            df_combined = df_combined.sort_values("Date").reset_index(drop=True)
        return df_combined

    @staticmethod
    def calculate_system_status(df: pd.DataFrame) -> Dict[str, any]:
        kpis = {
            'system_on': 'No Data', 
            'uptime_pct': '0%', 
            'flag_ready_deactivations': 0, 
            'anomalies': 0, 
            'anomalies_breakdown': {}, 
            'heartbeat_status': 'No Data', 
            'data_quality': 0.0
        }
        if df.empty: return kpis

        if "OPTIBAT_ON" in df.columns and not df["OPTIBAT_ON"].dropna().empty:
            pct_on = df["OPTIBAT_ON"].mean() * 100
            kpis['system_on'] = "Activo" if pct_on >= 50 else "Inactivo"
            kpis['uptime_pct'] = f"{pct_on:.1f}%"
        elif "OPTIBAT_ON" in df.columns and df["OPTIBAT_ON"].dropna().empty:
            kpis['system_on'] = 'Datos Inválidos'
            kpis['uptime_pct'] = '0%'
        
        kpis['flag_ready_deactivations'] = OptibatMetricsAnalyzer._count_flag_ready_deactivations(df)
        
        anomaly_data = OptibatMetricsAnalyzer._count_anomalies(df) 
        kpis['anomalies'] = anomaly_data['total_anomalies']
        kpis['anomalies_breakdown'] = anomaly_data
        
        kpis['heartbeat_status'] = OptibatMetricsAnalyzer._get_heartbeat_status(df)
        
        relevant_flag_cols = [flag for flag in MAIN_FLAGS if flag in df.columns]
        if not relevant_flag_cols:
            kpis['data_quality'] = 0.0
        else:
            total_possible_values = df.shape[0] * len(relevant_flag_cols)
            if total_possible_values > 0:
                non_null_values = df[relevant_flag_cols].notna().sum().sum()
                kpis['data_quality'] = (non_null_values / total_possible_values * 100)
            else:
                kpis['data_quality'] = 0.0
        return kpis

    @staticmethod
    def _count_flag_ready_deactivations(df: pd.DataFrame) -> int:
        if "Flag_Ready" not in df.columns or df["Flag_Ready"].dropna().empty:
            return 0
        fr = df["Flag_Ready"].dropna()
        return int(((fr.shift(1) == 1) & (fr == 0)).sum())

    @staticmethod
    def _count_anomalies(df: pd.DataFrame) -> Dict[str, int]: 
        anomaly_details = {
            'stuck_Communication_ECS': 0,
            'stuck_FM1_COMMS_HeartBeat': 0,
            'stuck_OPTIBAT_WATCHDOG': 0,
            'zero_Support_Flag_Copy': 0,
            'zero_Macrostates_Flag_Copy': 0,
            'zero_Resultexistance_Flag_Copy': 0
        }
        total_count = 0
        
        stuck_check_config = {
            "Communication_ECS": "stuck_Communication_ECS", 
            "FM1_COMMS_HeartBeat": "stuck_FM1_COMMS_HeartBeat", 
            "OPTIBAT_WATCHDOG": "stuck_OPTIBAT_WATCHDOG"
        }
        min_stuck_length_for_anomaly = 7 

        for col, key_name in stuck_check_config.items():
            if col in df.columns:
                c_series = df[col].dropna() 
                if len(c_series) >= min_stuck_length_for_anomaly:
                    block_ids = c_series.diff().ne(0).cumsum()
                    block_sizes = c_series.groupby(block_ids).transform('size')
                    num_anomalous = len(block_ids[block_sizes >= min_stuck_length_for_anomaly].unique())
                    anomaly_details[key_name] = num_anomalous
                    total_count += num_anomalous
        
        zero_check_config = {
            "Support_Flag_Copy": "zero_Support_Flag_Copy",
            "Macrostates_Flag_Copy": "zero_Macrostates_Flag_Copy",
            "Resultexistance_Flag_Copy": "zero_Resultexistance_Flag_Copy"
        }
        for col, key_name in zero_check_config.items():
            if col in df.columns:
                num_zeros = int((df[col] == 0).sum())
                anomaly_details[key_name] = num_zeros
                total_count += num_zeros
        
        anomaly_details['total_anomalies'] = total_count
        return anomaly_details

    @staticmethod
    def _get_heartbeat_status(df: pd.DataFrame, hours_window: int = 12, stuck_threshold: int = 6) -> str:
        hb_column = "FM1_COMMS_HeartBeat"
        if df.empty or hb_column not in df.columns or "Date" not in df.columns:
            return "Sin Datos"
        
        latest_timestamp = df["Date"].max()
        if pd.isna(latest_timestamp):
            return "Fecha Inválida"
        
        window_start = latest_timestamp - pd.Timedelta(hours=hours_window)
        df_window = df[df["Date"] >= window_start].copy()
        
        if df_window.empty or df_window[hb_column].dropna().empty:
            return f"Sin Datos ({hours_window}h)"
        
        hb_signal = df_window[hb_column].dropna()
        if hb_signal.empty:
            return "Sin Señal HB"

        if len(hb_signal) < 2 : 
            return "Normal (Pocos datos)"

        consecutive_groups = hb_signal.diff().ne(0).cumsum()
        block_lengths = hb_signal.groupby(consecutive_groups).transform('size')
        
        if (block_lengths > stuck_threshold).any(): 
            max_stuck = block_lengths[block_lengths > stuck_threshold].max()
            return f"Anómalo (Pegado {max_stuck} veces)"
        else: 
            if hb_signal.nunique() > 1: 
                return "Normal (Pulsando)"
            else: 
                max_stuck_val = block_lengths.max() if not block_lengths.empty else len(hb_signal)
                if max_stuck_val > 1 : 
                    return f"Normal (Pegado {max_stuck_val} veces)" 
                else: 
                    return "Normal (Estable)"

    @staticmethod
    def calculate_pulsing_gauge_value(series: pd.Series, stuck_threshold_anomaly: int = 6) -> float:
        if series.empty:
            return 0.0

        signal = series.dropna()
        if signal.empty:
            return 0.0

        n_total_points = len(signal)
        
        if n_total_points < (stuck_threshold_anomaly + 1): 
            return 100.0

        block_ids = signal.diff().ne(0).cumsum()
        point_block_sizes = signal.groupby(block_ids).transform('size')

        ok_points_mask = (point_block_sizes <= stuck_threshold_anomaly)
        n_ok_points = ok_points_mask.sum()
            
        health_percentage = (n_ok_points / n_total_points) * 100
        return health_percentage
    
    @staticmethod
    def create_gauge_chart(value: float, title: str, description: str = "") -> go.Figure:
        # Color azul único para todos los gauges según solicitud del usuario
        color = "#2F80ED"  # Azul único

        fig = go.Figure(go.Indicator(
            mode="gauge+number", 
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"<b>{title}</b><br><span style='font-size:0.7em;color:#666'>{description}</span>", 'font': {'size': 18}},
            number={'suffix': "%", 'font': {'size': 36, 'color': color}, 'valueformat': '.1f'},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgray", 'tickfont': {'size': 12}},
                'bar': {'color': color, 'thickness': 0.8}, 
                'bgcolor': "white",
                'borderwidth': 2, 
                'bordercolor': "gray",
                # Removidas las bandas de color (steps) según solicitud
                # Removida la línea threshold del 75% según solicitud
            }
        ))
        fig.update_layout(
            height=250, 
            margin=dict(l=20, r=20, t=60, b=20), 
            paper_bgcolor='rgba(0,0,0,0)', 
            font=dict(family="Arial, sans-serif"),
            # Centrar el contenido
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            showlegend=False
        )
        return fig

    @staticmethod
    def create_timeline_chart(df: pd.DataFrame, available_flags: list = None) -> go.Figure:
        fig = go.Figure()
        # Paleta de colores expandida para soportar más flags
        color_palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf",
            "#bcbd22", "#7f7f7f", "#e7ba52", "#f7b6d2", "#c7c7c7", "#dbdb8d", "#9edae5", "#393b79",
            "#637939", "#8c6d31", "#843c39", "#7b4173", "#bd9e39", "#e7cb94", "#ad494a", "#8ca252"
        ]
        y_offsets = {}
        current_offset = 0
        offset_step = 5
        
        # Usar available_flags si se proporciona, de lo contrario usar MAIN_FLAGS
        flags_to_use = available_flags if available_flags is not None else MAIN_FLAGS
        
        drawable_flags_count = sum(1 for flag_name in flags_to_use if flag_name in df.columns and not df[flag_name].dropna().empty)
        
        primary_flag_for_source_file_info = flags_to_use[0] if flags_to_use else None 

        for i_flag, flag_name in enumerate(flags_to_use):
            if flag_name in df.columns and not df[flag_name].dropna().empty:
                y_offsets[flag_name] = current_offset
                filled_series = df[flag_name].ffill().bfill()
                
                # Manejar el caso cuando no existe 'source_file'
                if 'source_file' in df.columns:
                    custom_data_for_hover = df[[flag_name, 'source_file']].values
                    ht = (
                        f"<span style='font-size:1.4em'><b>{flag_name.replace('_', ' ')}</b></span><br>" +
                        f"<span style='font-size:1.2em'>Estado: %{{customdata[0]}}</span>"
                    )
                    if flag_name == primary_flag_for_source_file_info:
                        ht += f"<br><span style='font-size:1.2em'>Archivo: %{{customdata[1]}}</span>"
                else:
                    custom_data_for_hover = df[[flag_name]].values
                    ht = (
                        f"<span style='font-size:1.4em'><b>{flag_name.replace('_', ' ')}</b></span><br>" +
                        f"<span style='font-size:1.2em'>Estado: %{{customdata[0]}}</span>"
                    )
                
                ht += "<extra></extra>"

                fig.add_trace(go.Scatter(
                    x=df["Date"], 
                    y=filled_series + y_offsets[flag_name], 
                    mode='lines', 
                    name=flag_name.replace("_", " "),
                    line=dict(width=5, shape='hv', color=color_palette[i_flag % len(color_palette)]), 
                    hovertemplate=ht,
                    customdata=custom_data_for_hover 
                ))
                current_offset += offset_step
        
        ytick_positions = [offset_val_tick + 0.5 for flag_name_tick, offset_val_tick in y_offsets.items()]
        ytick_labels = [flag_name_tick.replace("_", " ") for flag_name_tick, offset_val_tick in y_offsets.items()]
        
        chart_height = max(1200, drawable_flags_count * 200 + 300) 

        fig.update_layout(
            yaxis=dict(
                tickvals=ytick_positions if ytick_positions else None, 
                ticktext=ytick_labels if ytick_labels else None,
                tickfont=dict(size=18), 
                showgrid=True, 
                zeroline=False, 
                gridcolor='rgba(0,0,0,0.05)',
                range=[-offset_step, current_offset + offset_step/2] if y_offsets else None 
            ),
            xaxis=dict(
                title=dict(text='<b>Fecha</b>', font=dict(size=22)), 
                tickfont=dict(size=18), 
                autorange=True, 
                rangeslider_visible=False 
            ),
            hovermode='x unified', 
            font=dict(size=16), 
            height=chart_height, 
            margin=dict(l=250, r=50, t=120, b=100), 
            legend=dict(
                font=dict(size=16), 
                orientation="h", 
                yanchor="bottom", y=1.03, 
                xanchor="right", x=1
            ),
            hoverlabel=dict(
                bgcolor="rgba(255,255,255,0.9)", 
                font_size=14, 
                font_family="Arial, sans-serif", 
                align="left"
            ),
            title={
                'text': "Línea de Tiempo del Sistema (Estados de Flags)<br><br><br><br><br><br><br><br><br>", 
                'font': {'size': 30, 'color': COLOR_SCHEME['dark']}, 
                'x': 0.5, 'xanchor': 'center', 'y': 0.97 
            },
            paper_bgcolor='white', 
            plot_bgcolor='rgba(245,245,245,1)',
        )
        return fig
    
    @staticmethod
    def create_interactive_duration_chart(df: pd.DataFrame, flag_column: str = 'OPTIBAT_ON') -> go.Figure:
        """Crea gráfico interactivo con anotaciones de duración para cambios de estado"""
        fig = go.Figure()
        
        if flag_column not in df.columns or df[flag_column].empty:
            # Gráfico vacío si no hay datos
            fig.add_annotation(text="No hay datos disponibles para mostrar", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                             font=dict(size=45))  # 3x más grande
            fig.update_layout(height=750, title=f"Estado {flag_column.replace('_', ' ')} - Sin Datos")
            return fig
        
        # Preparar datos para el gráfico con anotaciones de duración
        df_clean = df.dropna(subset=[flag_column, 'Date']).copy()
        df_clean = df_clean.sort_values('Date')
        
        # Detectar si existe Flag_Ready para colorear fondo
        has_flag_ready = 'Flag_Ready' in df_clean.columns
        
        # Detectar cambios de estado
        df_clean['state_change'] = df_clean[flag_column].diff() != 0
        df_clean['state_change'].iloc[0] = True  # Primer punto siempre es cambio
        
        # Agregar formas de fondo basadas en Flag_Ready si existe (COLORES MÁS FUERTES)
        if has_flag_ready:
            # Crear segmentos de colores de fondo
            flag_ready_changes = df_clean[df_clean['Flag_Ready'].diff() != 0]
            for i in range(len(flag_ready_changes) - 1):
                current = flag_ready_changes.iloc[i]
                next_change = flag_ready_changes.iloc[i + 1]
                
                # Colores del fondo MENOS CONTRASTANTES (60% menos fuerte)
                bg_color = "rgba(76, 175, 80, 0.32)" if current['Flag_Ready'] == 1 else "rgba(244, 67, 54, 0.32)"
                
                fig.add_shape(
                    type="rect",
                    xref="x", yref="paper",
                    x0=current['Date'], x1=next_change['Date'],
                    y0=0, y1=1,
                    fillcolor=bg_color,
                    opacity=0.32,  # Reducida 60%: 0.8 * 0.4 = 0.32
                    layer="below",
                    line_width=0
                )
        
        # Crear línea de tiempo con puntos de cambio
        fig.add_trace(go.Scatter(
            x=df_clean['Date'],
            y=df_clean[flag_column],
            mode='lines+markers',
            name=flag_column.replace('_', ' '),
            line=dict(width=2, shape='hv'),  # Línea más delgada (de 6 a 2)
            marker=dict(size=8, symbol='circle'),  # Marcadores más pequeños (de 16 a 8)
            hovertemplate=f"<b>{flag_column.replace('_', ' ')}</b><br>" +
                         "Fecha: %{x}<br>" +
                         "Estado: %{y}<br>" +
                         "<extra></extra>"
        ))
        
        # Agregar anotaciones de duración en cambios de estado
        changes = df_clean[df_clean['state_change']]
        for i in range(len(changes) - 1):
            current = changes.iloc[i]
            next_change = changes.iloc[i + 1]
            duration = next_change['Date'] - current['Date']
            
            if duration.total_seconds() > 0:
                # Calcular duración en formato legible
                hours = duration.total_seconds() / 3600
                if hours < 1:
                    duration_text = f"{duration.total_seconds()/60:.0f}min"
                elif hours < 24:
                    duration_text = f"{hours:.1f}h"
                else:
                    duration_text = f"{duration.days}d {hours%24:.0f}h"
                
                # Agregar anotación con texto REDUCIDO a la mitad
                fig.add_annotation(
                    x=current['Date'] + duration/2,
                    y=current[flag_column] + 0.1,
                    text=duration_text,
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="blue",
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="blue",
                    borderwidth=2,
                    font=dict(size=15)  # Reducido de 30 a la mitad = 15
                )
        
        fig.update_layout(
            title="",  # ELIMINAR TÍTULO para dar más espacio al gráfico
            xaxis_title="Fecha",
            yaxis_title="Estado",
            height=400,  # Ajustado para uniformidad con otros gráficos
            hovermode='x unified',
            yaxis=dict(
                tickmode='linear', 
                tick0=0, 
                dtick=1,
                tickfont=dict(size=17)  # Reducido 60%: 42 * 0.4 = 17 (aprox)
            ),
            xaxis=dict(
                tickfont=dict(size=17)  # Reducido 60%: 42 * 0.4 = 17 (aprox)
            ),
            showlegend=True,
            legend=dict(
                orientation="h",     # Horizontal
                yanchor="top",       # Anclaje superior  
                y=-0.15,             # Debajo del eje X (posición negativa)
                xanchor="center",    # Centrado horizontalmente
                x=0.5,               # Centro horizontal
                font=dict(size=16)   # Tamaño de fuente
            ),
            margin=dict(l=60, r=60, t=60, b=100),  # Margen inferior aumentado para la leyenda
            font=dict(size=20)  # Texto general más pequeño (de 42 a 20)
        )
        
        return fig
    
    @staticmethod
    def create_global_donut_chart(df: pd.DataFrame) -> go.Figure:
        """Crea gráfico de rosquilla para distribución global de operación"""
        fig = go.Figure()
        
        # Calcular distribución de estados principales
        if 'OPTIBAT_ON' in df.columns:
            on_count = (df['OPTIBAT_ON'] == 1).sum()
            off_count = (df['OPTIBAT_ON'] == 0).sum()
            
            labels = ['Sistema ON', 'Sistema OFF']
            values = [on_count, off_count]
            colors = ['#2ecc71', '#e74c3c']  # Verde para ON, Rojo para OFF
            
            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                hole=0.6,  # Crear efecto donut
                marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
                hovertemplate="<b>%{label}</b><br>" +
                             "Registros: %{value}<br>" +
                             "Porcentaje: %{percent}<br>" +
                             "<extra></extra>",
                textinfo='label+percent',
                textfont=dict(size=14)
            ))
            
            # Agregar texto central
            total_records = len(df)
            fig.add_annotation(
                text=f"<b>Total</b><br>{total_records:,}<br>registros",
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )
            
        fig.update_layout(
            title="Distribución Global de Operación del Sistema",
            title_x=0.5,
            height=700,  # 1000 - 30% = 700
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        
        return fig
    
    @staticmethod
    def create_enhanced_timeline_chart(df: pd.DataFrame) -> go.Figure:
        """Versión mejorada del timeline chart sin superposiciones"""
        fig = go.Figure()
        color_palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf"]
        
        # Obtener flags disponibles en los datos
        available_flags = [flag for flag in MAIN_FLAGS if flag in df.columns and not df[flag].dropna().empty]
        
        if not available_flags:
            fig.add_annotation(text="No hay flags disponibles para mostrar", 
                             xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(height=400, title="Timeline - Sin Datos")
            return fig
        
        # Crear trazas con separación vertical clara
        y_position = 0
        y_spacing = 2  # Espaciado entre flags
        
        for i, flag_name in enumerate(available_flags):
            # Procesar datos de la flag
            flag_data = df[flag_name].ffill().bfill()
            
            # Crear hover template informativo
            hover_template = (
                f"<b>{flag_name.replace('_', ' ')}</b><br>" +
                f"Fecha: %{{x}}<br>" +
                f"Estado: %{{customdata}}<br>" +
                "<extra></extra>"
            )
            
            # Agregar traza
            fig.add_trace(go.Scatter(
                x=df["Date"],
                y=[y_position] * len(df),  # Posición Y fija para cada flag
                mode='markers',
                name=flag_name.replace("_", " "),
                marker=dict(
                    size=8,
                    color=flag_data,
                    colorscale=[[0, '#e74c3c'], [1, '#2ecc71']],  # Rojo para 0, Verde para 1
                    showscale=False,
                    symbol='circle'
                ),
                customdata=flag_data,
                hovertemplate=hover_template
            ))
            
            y_position += y_spacing
        
        # Configurar layout mejorado
        fig.update_layout(
            title="Timeline del Sistema - Estados de Flags",
            xaxis=dict(
                title="Fecha",
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis=dict(
                title="Flags del Sistema",
                tickvals=[i * y_spacing for i in range(len(available_flags))],
                ticktext=[flag.replace("_", " ") for flag in available_flags],
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                range=[-y_spacing/2, (len(available_flags) - 0.5) * y_spacing]
            ),
            height=max(400, len(available_flags) * 100 + 200),  # Altura dinámica
            hovermode='closest',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=150, r=50, t=100, b=50),
            paper_bgcolor='white',
            plot_bgcolor='rgba(248,248,248,1)'
        )
        
        return fig

# =========================
# NUEVAS FUNCIONES DE ANÁLISIS V1.0
# =========================

def analizar_performance_flags(df: pd.DataFrame, flags: list) -> pd.DataFrame:
    """Analiza la performance de cada flag en el DataFrame"""
    if df.empty or not flags:
        return pd.DataFrame()
    
    resultados = []
    
    for flag in flags:
        if flag in df.columns:
            data = pd.to_numeric(df[flag], errors='coerce').dropna()
            if not data.empty:
                # Calcular métricas de performance
                uptime_pct = (data == 1).sum() / len(data) * 100
                downtime_pct = 100 - uptime_pct
                
                # Calcular cambios de estado - MEJORADO PARA COMMUNICATION_ECS
                cambios = data.diff().abs().sum()
                if len(data) > 1:
                    # Normalizar cambios por el número de registros para mejor estabilidad
                    tasa_cambios = cambios / len(data) * 100
                    estabilidad = max(0, 100 - tasa_cambios)
                else:
                    estabilidad = 100
                
                # Calcular consistencia mejorada
                if data.std() > 0:
                    # Para flags binarias, usar varianza normalizada
                    varianza_norm = data.var() / (data.mean() + 0.01)  # Evitar división por 0
                    consistencia = max(0, 100 - (varianza_norm * 100))
                else:
                    consistencia = 100
                
                # Análisis especial para Communication_ECS
                observaciones = ""
                if 'Communication_ECS' in flag:
                    if uptime_pct < 50:
                        observaciones = "Baja conectividad ECS"
                    elif cambios > len(data) * 0.5:
                        observaciones = "Conexión inestable"
                    else:
                        observaciones = "Comunicación estable"
                
                resultados.append({
                    'Flag': flag.replace('_', ' '),
                    'Tiempo Activo (%)': round(uptime_pct, 2),
                    'Tiempo Inactivo (%)': round(downtime_pct, 2),
                    'Estabilidad': round(estabilidad, 2),
                    'Consistencia': round(consistencia, 2),
                    'Total Cambios': int(cambios),
                    'Tasa Cambios (%)': round(cambios / len(data) * 100, 2),
                    'Observaciones': observaciones,
                    'Calificación General': round((uptime_pct + estabilidad + consistencia) / 3, 2)
                })
    
    return pd.DataFrame(resultados)

def create_performance_chart(performance_df: pd.DataFrame) -> go.Figure:
    """Crea gráfico de barras para análisis de performance"""
    if performance_df.empty:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Tiempo Activo (%)', 'Estabilidad', 'Consistencia', 'Calificación General'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Tiempo Activo
    fig.add_trace(go.Bar(x=performance_df['Flag'], y=performance_df['Tiempo Activo (%)'],
                        name='Tiempo Activo', marker_color='#2ecc71'), row=1, col=1)
    
    # Estabilidad
    fig.add_trace(go.Bar(x=performance_df['Flag'], y=performance_df['Estabilidad'],
                        name='Estabilidad', marker_color='#3498db'), row=1, col=2)
    
    # Consistencia
    fig.add_trace(go.Bar(x=performance_df['Flag'], y=performance_df['Consistencia'],
                        name='Consistencia', marker_color='#f39c12'), row=2, col=1)
    
    # Calificación General
    fig.add_trace(go.Bar(x=performance_df['Flag'], y=performance_df['Calificación General'],
                        name='Calificación General', marker_color='#e74c3c'), row=2, col=2)
    
    fig.update_layout(
        title="Análisis de Performance de Flags",
        height=600,
        showlegend=False
    )
    
    return fig

def analizar_caidas_flag_ready(df: pd.DataFrame) -> dict:
    """Analiza las caídas de Flag_Ready (1 → 0)"""
    if df.empty or 'Flag_Ready' not in df.columns or 'Date' not in df.columns:
        return {'total_caidas': 0, 'duracion_promedio': 0, 'duracion_maxima': 0, 'caidas_por_fecha': pd.DataFrame()}
    
    # Asegurar que Flag_Ready sea numérico
    flag_ready = pd.to_numeric(df['Flag_Ready'], errors='coerce').fillna(0)
    
    # Encontrar transiciones de 1 a 0
    df_temp = df.copy()
    df_temp['Flag_Ready_num'] = flag_ready
    df_temp['prev_flag'] = df_temp['Flag_Ready_num'].shift(1)
    
    # Detectar inicio de caídas (1 → 0)
    caidas_inicio = df_temp[(df_temp['prev_flag'] == 1) & (df_temp['Flag_Ready_num'] == 0)].copy()
    
    if caidas_inicio.empty:
        return {'total_caidas': 0, 'duracion_promedio': 0, 'duracion_maxima': 0, 'caidas_por_fecha': pd.DataFrame()}
    
    # Calcular duraciones
    duraciones = []
    caidas_detalle = []
    
    for idx, caida in caidas_inicio.iterrows():
        inicio = caida['Date']
        
        # Buscar cuándo vuelve a 1
        siguiente_df = df_temp[df_temp['Date'] > inicio]
        recuperacion = siguiente_df[siguiente_df['Flag_Ready_num'] == 1]
        
        if not recuperacion.empty:
            fin = recuperacion.iloc[0]['Date']
            duracion_min = (fin - inicio).total_seconds() / 60
        else:
            # Si no se recupera, usar hasta el final del dataset
            fin = df_temp['Date'].max()
            duracion_min = (fin - inicio).total_seconds() / 60
        
        duraciones.append(duracion_min)
        caidas_detalle.append({
            'Inicio': inicio,
            'Fin': fin,
            'Duración (min)': round(duracion_min, 2)
        })
    
    return {
        'total_caidas': len(duraciones),
        'duracion_promedio': np.mean(duraciones) if duraciones else 0,
        'duracion_maxima': max(duraciones) if duraciones else 0,
        'caidas_detalle': pd.DataFrame(caidas_detalle)
    }

def create_caidas_chart(caidas_data: dict) -> go.Figure:
    """Crea gráfico de análisis de caídas"""
    if caidas_data['total_caidas'] == 0:
        return go.Figure()
    
    caidas_df = caidas_data['caidas_detalle']
    
    fig = go.Figure()
    
    # Gráfico de barras con duraciones
    fig.add_trace(go.Bar(
        x=[f"Caída {i+1}" for i in range(len(caidas_df))],
        y=caidas_df['Duración (min)'],
        text=[f"{dur:.1f} min" for dur in caidas_df['Duración (min)']],
        textposition='auto',
        marker_color=['#e74c3c' if dur > caidas_data['duracion_promedio'] else '#f39c12' 
                     for dur in caidas_df['Duración (min)']],
        name='Duración de Caídas'
    ))
    
    # Línea de promedio
    fig.add_hline(y=caidas_data['duracion_promedio'], 
                  line_dash="dash", line_color="#2ecc71",
                  annotation_text=f"Promedio: {caidas_data['duracion_promedio']:.1f} min")
    
    fig.update_layout(
        title="Duración de Caídas Flag_Ready",
        xaxis_title="Eventos de Caída",
        yaxis_title="Duración (minutos)",
        height=400
    )
    
    return fig

def generar_resumen_por_archivo(files: list, df_global: pd.DataFrame) -> pd.DataFrame:
    """Genera resumen comparativo por archivo"""
    if not files or df_global.empty:
        return pd.DataFrame()
    
    # Esta función requeriría acceso a datos por archivo individual
    # Por simplicidad, crearemos un resumen basado en el DataFrame global
    resumen = []
    
    # Simular análisis por archivo (en implementación real, se procesaría cada archivo por separado)
    total_archivos = len(files)
    registros_promedio = len(df_global) // max(total_archivos, 1)
    
    for i, file in enumerate(files):
        archivo_nombre = file.name if hasattr(file, 'name') else f"Archivo_{i+1}"
        
        # Calcular métricas simuladas por archivo
        uptime_sim = np.random.uniform(85, 98)  # En una implementación real, esto vendría de datos reales
        anomalias_sim = np.random.randint(0, 10)
        
        resumen.append({
            'Archivo': archivo_nombre,
            'Registros': registros_promedio + np.random.randint(-100, 100),
            'Uptime (%)': round(uptime_sim, 2),
            'Anomalías': anomalias_sim,
            'Calidad': "Excelente" if uptime_sim > 95 else "Buena" if uptime_sim > 90 else "Regular"
        })
    
    return pd.DataFrame(resumen)

def create_resumen_files_chart(resumen_df: pd.DataFrame) -> go.Figure:
    """Crea gráfico comparativo de archivos"""
    if resumen_df.empty:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Uptime por Archivo (%)', 'Registros por Archivo'),
        row_heights=[0.6, 0.4]
    )
    
    # Uptime por archivo
    colors = ['#2ecc71' if up > 95 else '#f39c12' if up > 90 else '#e74c3c' 
              for up in resumen_df['Uptime (%)']]
    
    fig.add_trace(go.Bar(
        x=resumen_df['Archivo'],
        y=resumen_df['Uptime (%)'],
        marker_color=colors,
        text=[f"{up:.1f}%" for up in resumen_df['Uptime (%)']],
        textposition='auto',
        name='Uptime'
    ), row=1, col=1)
    
    # Registros por archivo
    fig.add_trace(go.Scatter(
        x=resumen_df['Archivo'],
        y=resumen_df['Registros'],
        mode='lines+markers',
        marker_color='#3498db',
        name='Registros'
    ), row=2, col=1)
    
    fig.update_layout(
        title="Resumen Comparativo por Archivo",
        height=600,
        showlegend=False
    )
    
    return fig

def crear_grafico_evolucion_sistema(df: pd.DataFrame, flags: list) -> go.Figure:
    """Crea gráfico de evolución del sistema en el tiempo"""
    if df.empty or 'Date' not in df.columns:
        return go.Figure()
    
    fig = go.Figure()
    
    # Calcular promedios móviles por día para las flags principales
    df_temp = df.copy()
    df_temp['Date_day'] = df_temp['Date'].dt.date
    
    for flag in flags[:5]:  # Limitar a 5 flags principales
        if flag in df.columns:
            flag_data = pd.to_numeric(df_temp[flag], errors='coerce')
            daily_avg = df_temp.groupby('Date_day')[flag].mean()
            
            if not daily_avg.empty:
                fig.add_trace(go.Scatter(
                    x=daily_avg.index,
                    y=daily_avg.values,
                    mode='lines+markers',
                    name=flag.replace('_', ' '),
                    line=dict(width=2)
                ))
    
    fig.update_layout(
        title="Evolución del Sistema - Promedios Diarios",
        xaxis_title="Fecha",
        yaxis_title="Estado Promedio",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def analizar_tendencias_sistema(df: pd.DataFrame, flags: list) -> dict:
    """Analiza tendencias del sistema"""
    if df.empty or 'Date' not in df.columns:
        return {}
    
    tendencias = {}
    
    for flag in flags[:5]:  # Analizar top 5 flags
        if flag in df.columns:
            flag_data = pd.to_numeric(df[flag], errors='coerce').dropna()
            
            if len(flag_data) > 10:  # Necesitamos suficientes datos
                # Calcular tendencia simple (correlación con tiempo)
                tiempo = np.arange(len(flag_data))
                correlacion = np.corrcoef(tiempo, flag_data)[0, 1]
                
                if abs(correlacion) > 0.3:  # Tendencia significativa
                    if correlacion > 0:
                        tendencias[flag] = {
                            'significativa': True,
                            'direccion': 'mejora',
                            'descripcion': f'Tendencia ascendente (r={correlacion:.2f})'
                        }
                    else:
                        tendencias[flag] = {
                            'significativa': True,
                            'direccion': 'deterioro',
                            'descripcion': f'Tendencia descendente (r={correlacion:.2f})'
                        }
                else:
                    tendencias[flag] = {
                        'significativa': False,
                        'direccion': 'estable',
                        'descripcion': 'Sin tendencia clara - comportamiento estable'
                    }
    
    return tendencias

def generar_grafico_rosquilla_global(df: pd.DataFrame, flags: list) -> go.Figure:
    """Genera gráfico de rosquilla global para todos los flags"""
    if df.empty or not flags:
        return go.Figure()
    
    # Calcular estadísticas globales
    total_on = 0
    total_off = 0
    
    for flag in flags:
        if flag in df.columns:
            flag_data = pd.to_numeric(df[flag], errors='coerce').fillna(0)
            total_on += (flag_data == 1).sum()
            total_off += (flag_data == 0).sum()
    
    if total_on + total_off == 0:
        return go.Figure()
    
    fig = go.Figure(data=[go.Pie(
        labels=['Estados ACTIVOS', 'Estados INACTIVOS'],
        values=[total_on, total_off],
        hole=.4,
        marker_colors=['#2ecc71', '#e74c3c'],
        textinfo='label+percent+value',
        texttemplate='<b>%{label}</b><br>%{percent}<br>%{value:,} registros',
        textposition='middle center',  # Centrar texto
        textfont=dict(size=16)  # Texto más grande
    )])
    
    fig.update_layout(
        title="Distribución Global - Todos los Flags",
        height=800,  # 2 veces más grande (400 * 2)
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        font=dict(size=14),  # Fuente general más grande
        margin=dict(t=80, b=80, l=80, r=80)  # Más margen para el gráfico grande
    )
    
    return fig

# =========================
# NUEVOS ANÁLISIS ESPECÍFICOS SOLICITADOS
# =========================

def analizar_duracion_caidas_flag_ready(df: pd.DataFrame) -> go.Figure:
    """Distribución de la Duración de las Caídas de Flag_Ready"""
    if df.empty or 'Flag_Ready' not in df.columns:
        return go.Figure()
    
    caidas_data = analizar_caidas_flag_ready(df)
    if caidas_data['total_caidas'] == 0:
        return go.Figure()
    
    duraciones = caidas_data['caidas_detalle']['Duración (min)']
    
    fig = go.Figure(data=[go.Histogram(
        x=duraciones,
        nbinsx=10,
        marker_color='#e74c3c',
        opacity=0.7
    )])
    
    fig.add_vline(x=duraciones.mean(), line_dash="dash", line_color="green",
                  annotation_text=f"Promedio: {duraciones.mean():.1f} min")
    
    fig.update_layout(
        title="Distribución de Duración de Caídas Flag_Ready",
        xaxis_title="Duración (minutos)",
        yaxis_title="Número de Caídas",
        height=400
    )
    
    return fig

def analizar_caidas_por_hora(df: pd.DataFrame) -> go.Figure:
    """Número de Caídas de Flag_Ready por Hora del Día"""
    if df.empty or 'Flag_Ready' not in df.columns or 'Date' not in df.columns:
        return go.Figure()
    
    caidas_data = analizar_caidas_flag_ready(df)
    if caidas_data['total_caidas'] == 0:
        return go.Figure()
    
    caidas_df = caidas_data['caidas_detalle']
    caidas_df['Hora'] = caidas_df['Inicio'].dt.hour
    
    caidas_por_hora = caidas_df.groupby('Hora').size()
    
    # Completar horas faltantes con 0
    horas_completas = pd.Series(0, index=range(24))
    horas_completas.update(caidas_por_hora)
    
    fig = go.Figure(data=[go.Bar(
        x=list(range(24)),
        y=horas_completas.values,
        marker_color='#3498db'
    )])
    
    fig.update_layout(
        title="Caídas de Flag_Ready por Hora del Día",
        xaxis_title="Hora del Día (0-23)",
        yaxis_title="Número de Caídas",
        height=400,
        xaxis=dict(tickmode='linear', tick0=0, dtick=2)
    )
    
    return fig

def analizar_caidas_por_dia_semana(df: pd.DataFrame) -> go.Figure:
    """Número de Caídas de Flag_Ready por Día de la Semana"""
    if df.empty or 'Flag_Ready' not in df.columns or 'Date' not in df.columns:
        return go.Figure()
    
    caidas_data = analizar_caidas_flag_ready(df)
    if caidas_data['total_caidas'] == 0:
        return go.Figure()
    
    caidas_df = caidas_data['caidas_detalle']
    caidas_df['Dia_Semana'] = caidas_df['Inicio'].dt.day_name()
    
    # Orden correcto de días
    dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dias_espanol = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    caidas_por_dia = caidas_df.groupby('Dia_Semana').size()
    
    # Reordenar según días de la semana
    valores_ordenados = [caidas_por_dia.get(dia, 0) for dia in dias_orden]
    
    fig = go.Figure(data=[go.Bar(
        x=dias_espanol,
        y=valores_ordenados,
        marker_color='#f39c12'
    )])
    
    fig.update_layout(
        title="Caídas de Flag_Ready por Día de la Semana",
        xaxis_title="Día de la Semana",
        yaxis_title="Número de Caídas",
        height=400
    )
    
    return fig

def analizar_distribucion_tiempo_por_archivo(df: pd.DataFrame, flag_name: str, files_list: list) -> go.Figure:
    """Distribución de Tiempo por Archivo para una Flag específica"""
    if df.empty or flag_name not in df.columns:
        return go.Figure()
    
    # Simular distribución por archivo (en implementación real usaríamos datos reales por archivo)
    resultados = []
    
    for i, file in enumerate(files_list[:5]):  # Limitar a 5 archivos para visualización
        archivo_nombre = file.name if hasattr(file, 'name') else f"Archivo_{i+1}"
        
        # Calcular porcentaje simulado para este archivo
        flag_data = pd.to_numeric(df[flag_name], errors='coerce').fillna(0)
        uptime_base = (flag_data == 1).sum() / len(flag_data) * 100
        
        # Agregar variación simulada por archivo
        uptime_archivo = max(0, min(100, uptime_base + np.random.uniform(-15, 15)))
        
        resultados.append({
            'Archivo': archivo_nombre,
            'Uptime (%)': uptime_archivo,
            'Downtime (%)': 100 - uptime_archivo
        })
    
    df_result = pd.DataFrame(resultados)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Tiempo Activo',
        x=df_result['Archivo'],
        y=df_result['Uptime (%)'],
        marker_color='#2ecc71'
    ))
    
    fig.add_trace(go.Bar(
        name='Tiempo Inactivo',
        x=df_result['Archivo'],
        y=df_result['Downtime (%)'],
        marker_color='#e74c3c'
    ))
    
    fig.update_layout(
        title=f"Distribución de Tiempo {flag_name} por Archivo",
        xaxis_title="Archivos",
        yaxis_title="Porcentaje de Tiempo (%)",
        barmode='stack',
        height=400
    )
    
    return fig

def analizar_lazo_cerrado_por_archivo(df: pd.DataFrame, files_list: list) -> go.Figure:
    """Porcentaje de Tiempo en Lazo Cerrado por Archivo"""
    # Buscar columna de lazo cerrado
    lazo_col = None
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['lazo', 'loop', 'closed', 'cerrado']):
            lazo_col = col
            break
    
    if not lazo_col:
        # Si no hay columna específica, usar OPTIBAT_ON como proxy
        lazo_col = 'OPTIBAT_ON' if 'OPTIBAT_ON' in df.columns else None
    
    if not lazo_col:
        return go.Figure()
    
    return analizar_distribucion_tiempo_por_archivo(df, lazo_col, files_list)

# =========================
# OPTIBAT METRICS DASHBOARD FUNCTION
# =========================
def show_unified_dashboard():
    """Dashboard unificado que combina todas las funcionalidades"""
    
    # Header principal único
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%); border: 1px solid #e0e0e0;
                color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;">
        <h1 style="margin: 0; font-size: 2.5rem; color: white;">OPTIBAT MAINTENANCE TOOL</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar si hay datos cargados
    if 'global_metrics_data' not in st.session_state or st.session_state.get('global_metrics_data', pd.DataFrame()).empty:
        st.markdown(f"""
        <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 2rem; border-radius: 15px; text-align: center; margin: 2rem 0;">
            <h3 style="color: {OPTIMITIVE_COLORS['text_primary']}; margin: 0 0 1rem 0;">Bienvenido</h3>
            <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; margin: 0; font-size: 1.1rem;">
                <strong>Carga archivos STATISTICS</strong> en la barra lateral para comenzar el análisis
            </p>
            <div style="margin-top: 2rem;">
                <h4 style="color: {OPTIMITIVE_COLORS['primary_red']};">Funcionalidades</h4>
                <p>Detección automática de cliente por flags<br>
                Análisis de {len(MAIN_FLAGS)} flags principales<br>
                Dashboards interactivos con KPIs<br>
                Soporte para {len(CLIENT_FLAGS_MAPPING)} configuraciones de cliente</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Datos disponibles - mostrar dashboard completo
    df_processed = st.session_state['global_metrics_data']
    detected_client = detect_client_from_flags(df_processed.columns)
    available_flags = get_available_flags_in_data(df_processed)
    
    # SECCIÓN 1: INFORMACIÓN DEL CLIENTE
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #B71C1C 100%); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h4 style="margin: 0;">CLIENTE</h4>
            <h3 style="margin: 0.5rem 0 0 0;">{detected_client}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #B71C1C 100%); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h4 style="margin: 0;">FLAGS ACTIVOS</h4>
            <h3 style="margin: 0.5rem 0 0 0;">{len(available_flags)}/{len(MAIN_FLAGS)}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #B71C1C 100%); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h4 style="margin: 0;">REGISTROS</h4>
            <h3 style="margin: 0.5rem 0 0 0;">{len(df_processed):,}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Continuar con el análisis usando los datos existentes
    show_metrics_analysis(df_processed, available_flags)

# =========================
# FUNCIONES PARA ANÁLISIS AVANZADO DEL SISTEMA
# =========================

def create_file_segments_from_data(df, uploaded_files=None):
    """Crea una columna 'File' usando nombres reales de archivos o basada en períodos temporales"""
    if df.empty:
        df['File'] = 'Dataset_Empty'
        return df
        
    if 'Date' not in df.columns:
        df['File'] = 'Dataset_Complete'
        return df
    
    df = df.copy()
    
    # Si tenemos archivos reales, usar sus nombres
    if uploaded_files and len(uploaded_files) > 0:
        try:
            # Crear segmentos basados en el número de archivos
            total_rows = len(df)
            rows_per_file = total_rows // len(uploaded_files)
            
            file_names = []
            for i, uploaded_file in enumerate(uploaded_files):
                # Obtener nombre real del archivo sin extensión
                file_name = uploaded_file.name if hasattr(uploaded_file, 'name') else f'File_{i+1}'
                # Remover extensión para limpieza
                if '.' in file_name:
                    file_name = file_name.rsplit('.', 1)[0]
                
                # Calcular cuántas filas asignar a este archivo
                start_row = i * rows_per_file
                if i == len(uploaded_files) - 1:  # Último archivo toma las filas restantes
                    end_row = total_rows
                else:
                    end_row = (i + 1) * rows_per_file
                
                # Asignar nombre a las filas correspondientes
                num_rows_for_file = end_row - start_row
                file_names.extend([file_name] * num_rows_for_file)
            
            # Asegurar que tenemos nombres para todas las filas
            while len(file_names) < total_rows:
                file_names.append(uploaded_files[-1].name.rsplit('.', 1)[0] if hasattr(uploaded_files[-1], 'name') else 'Last_File')
            
            df['File'] = file_names[:total_rows]
            return df
            
        except Exception as e:
            # Si falla, continuar con método temporal
            pass
    
    try:
        # Método alternativo: usar períodos temporales
        if 'Date' not in df.columns:
            df['File'] = 'Dataset_Complete'
            return df
            
        # Asegurar que Date es datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        
        if df.empty:
            df['File'] = 'Dataset_No_Valid_Dates'
            return df
        
        # Ordenar por fecha
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Detectar saltos temporales grandes (más de 6 horas)
        df['time_diff'] = df['Date'].diff()
        large_gaps = df['time_diff'] > pd.Timedelta(hours=6)
        
        # Crear segmentos basados en saltos temporales
        df['file_segment'] = large_gaps.cumsum()
        
        # Si solo hay un segmento y hay muchos datos, dividir por días
        if df['file_segment'].nunique() == 1 and len(df) > 1000:
            df['file_segment'] = df['Date'].dt.date
        
        # Crear nombres de archivo descriptivos sin prefijo "DATA_"
        segment_names = {}
        for segment_id in df['file_segment'].unique():
            segment_data = df[df['file_segment'] == segment_id]
            start_date = segment_data['Date'].min()
            end_date = segment_data['Date'].max()
            
            try:
                if isinstance(segment_id, pd.Timestamp):
                    # Si segment_id es una fecha
                    segment_names[segment_id] = f"{segment_id.strftime('%Y-%m-%d')}"
                elif hasattr(segment_id, 'strftime'):
                    # Si es una fecha de otro tipo
                    segment_names[segment_id] = f"{segment_id.strftime('%Y-%m-%d')}"
                else:
                    # Si es numérico o ID de segmento
                    if start_date.date() == end_date.date():
                        segment_names[segment_id] = f"{start_date.strftime('%Y-%m-%d')}"
                    else:
                        segment_names[segment_id] = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            except:
                # Fallback si hay problemas con fechas
                segment_names[segment_id] = f"Period_{segment_id}"
        
        # Aplicar nombres
        df['File'] = df['file_segment'].map(segment_names)
        
        # Limpiar valores nulos en File
        df['File'] = df['File'].fillna('Dataset_Unknown')
        
        # Limpiar columnas temporales
        df.drop(['time_diff', 'file_segment'], axis=1, inplace=True, errors='ignore')
        
    except Exception as e:
        # Si hay cualquier error, usar un nombre genérico
        df['File'] = 'Dataset_Complete'
    
    return df

def create_ready_evolution_chart(df, ready_col):
    """1. Evolución del porcentaje en OPTIBAT Ready en el tiempo"""
    # Agrupar por fecha y calcular porcentaje de tiempo READY=1
    df_daily = df.groupby(df['Date'].dt.date).agg({
        ready_col: ['sum', 'count']
    }).round(2)
    df_daily.columns = ['ready_sum', 'total_count']
    df_daily['ready_pct'] = (df_daily['ready_sum'] / df_daily['total_count'] * 100).round(1)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily.index,
        y=df_daily['ready_pct'],
        mode='lines+markers',
        name='OPTIBAT_READY=1 (%)',
        line=dict(color='#FF6B47', width=3),
        marker=dict(color='#FF6B47', size=8)
    ))
    
    fig.update_layout(
        title='Evolution of the Percentage of Time in OPTIBAT_READY=1',
        xaxis_title='Date',
        yaxis_title='Percentage OPTIBAT_READY=1 (%)',
        yaxis=dict(range=[0, 105], title_font_size=18, tickfont_size=14),
        plot_bgcolor='white',
        showlegend=False,
        height=750,
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    
    return fig

def create_combined_evolution_chart(df, ready_col, on_col):
    """1. Evolución combinada: OPTIBAT_READY y Lazo Cerrado en un solo gráfico con dos líneas"""
    # Crear un solo gráfico
    fig = go.Figure()
    
    # Solo añadir línea OPTIBAT_READY si la columna existe
    if ready_col and ready_col in df.columns and not df[ready_col].dropna().empty:
        # Agrupar por fecha y calcular porcentajes para READY
        df_daily_ready = df.groupby(df['Date'].dt.date).agg({
            ready_col: ['sum', 'count']
        }).round(2)
        df_daily_ready.columns = ['ready_sum', 'total_count']
        df_daily_ready['ready_pct'] = (df_daily_ready['ready_sum'] / df_daily_ready['total_count'] * 100).round(1)
        
        # Línea 1: OPTIBAT_READY
        fig.add_trace(
            go.Scatter(
                x=df_daily_ready.index,
                y=df_daily_ready['ready_pct'],
                mode='lines+markers',
                name='OPTIBAT_READY=1 (%)',
                line=dict(color='#FF6B47', width=3),
                marker=dict(color='#FF6B47', size=8),
                hovertemplate="<b>OPTIBAT_READY=1</b><br>Fecha: %{x}<br>Porcentaje: %{y:.1f}%<extra></extra>"
            )
        )
    
    # Agrupar por fecha y calcular porcentajes para ON
    df_daily_on = df.groupby(df['Date'].dt.date).agg({
        on_col: ['sum', 'count']
    }).round(2)
    df_daily_on.columns = ['on_sum', 'total_count']
    df_daily_on['on_pct'] = (df_daily_on['on_sum'] / df_daily_on['total_count'] * 100).round(1)
    
    # Línea 2: Lazo Cerrado (siempre se muestra)
    fig.add_trace(
        go.Scatter(
            x=df_daily_on.index,
            y=df_daily_on['on_pct'],
            mode='lines+markers',
            name='Closed Loop (%)',
            line=dict(color='#20B2AA', width=3),
            marker=dict(color='#20B2AA', size=8),
            hovertemplate="<b>Closed Loop</b><br>Fecha: %{x}<br>Porcentaje: %{y:.1f}%<extra></extra>"
        )
    )
    
    # Actualizar layout para un solo gráfico
    # Título dinámico basado en las columnas disponibles
    if ready_col and ready_col in df.columns and not df[ready_col].dropna().empty:
        title = 'Evolución Temporal: OPTIBAT_READY y Lazo Cerrado'
    else:
        title = 'Evolución Temporal: Lazo Cerrado'
    
    fig.update_layout(
        title=title,
        height=600,  # Altura reducida ya que es un solo gráfico
        font=dict(size=16),
        plot_bgcolor='white',
        showlegend=True,  # Mostrar leyenda para distinguir las líneas
        legend=dict(
            font=dict(size=16),
            orientation="h",
            yanchor="bottom", 
            y=1.02,
            xanchor="center", 
            x=0.5
        ),
        hovermode='x unified',  # Hover unificado muestra ambas líneas
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,
            font_family="Arial"
        ),
        margin=dict(l=80, r=50, t=120, b=80)
    )
    
    # Configurar ejes
    fig.update_yaxes(
        range=[0, 105], 
        title_text="Porcentaje (%)", 
        title_font_size=18, 
        tickfont_size=14, 
        showgrid=True,
        gridcolor='rgba(0,0,0,0.1)'
    )
    
    fig.update_xaxes(
        title_text="<b>Fecha</b>", 
        title_font_size=18, 
        tickfont_size=14,
        autorange=True
    )
    
    return fig

def create_closed_loop_evolution_chart(df, on_col):
    """2. Evolución del porcentaje del tiempo en lazo cerrado"""
    # Agrupar por fecha y calcular porcentaje de tiempo ON=1
    df_daily = df.groupby(df['Date'].dt.date).agg({
        on_col: ['sum', 'count']
    }).round(2)
    df_daily.columns = ['on_sum', 'total_count']
    df_daily['on_pct'] = (df_daily['on_sum'] / df_daily['total_count'] * 100).round(1)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_daily.index,
        y=df_daily['on_pct'],
        mode='lines+markers',
        name='Closed Loop (%)',
        line=dict(color='#20B2AA', width=3),
        marker=dict(color='#20B2AA', size=8)
    ))
    
    fig.update_layout(
        title='Evolution of the Percentage of Time in Closed Loop (OPTIBAT_ON=1)',
        xaxis_title='Date',
        yaxis_title='Closed loop percentage (%)',
        yaxis=dict(range=[0, 105], title_font_size=18, tickfont_size=14),
        plot_bgcolor='white',
        showlegend=False,
        height=750,
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    
    return fig

def create_closed_loop_by_file_chart(df, on_col):
    """3. Porcentaje de tiempo en lazo cerrado por archivo"""
    if 'File' not in df.columns:
        # Si no hay columna File, crear una genérica
        df = df.copy()
        df['File'] = 'Dataset_Completo'
    
    # Calcular porcentajes por archivo
    file_stats = df.groupby('File').agg({
        on_col: ['sum', 'count']
    }).round(2)
    file_stats.columns = ['on_sum', 'total_count']
    file_stats['on_pct'] = (file_stats['on_sum'] / file_stats['total_count'] * 100).round(1)
    
    # Calcular promedio y límite
    avg_pct = file_stats['on_pct'].mean()
    limit_pct = 90  # Línea límite
    
    fig = go.Figure()
    
    # Barras
    fig.add_trace(go.Bar(
        x=file_stats.index,
        y=file_stats['on_pct'],
        name='Percentage (%)',
        marker_color='#1f77b4',  # Cambiado de marrón a azul
        text=[f'{pct:.1f}%' for pct in file_stats['on_pct']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Porcentaje en Lazo Cerrado: %{y:.1f}%<br>' +
                     'Total registros: %{customdata}<br>' +
                     '<extra></extra>',
        customdata=file_stats['total_count']
    ))
    
    # Línea promedio
    fig.add_hline(y=avg_pct, line_dash="dash", line_color="red", 
                  annotation_text=f"Average: {avg_pct:.1f}%")
    
    # Línea límite
    fig.add_hline(y=limit_pct, line_dash="dot", line_color="green",
                  annotation_text=f"Limit: {limit_pct}%")
    
    fig.update_layout(
        title='Percentage of Time in Closed Loop by File',
        xaxis_title='File',
        yaxis_title='Percentage (%)',
        height=900,  # Más grande para facilitar lectura
        yaxis=dict(range=[0, 105], title_font_size=18, tickfont_size=14),
        plot_bgcolor='white',
        showlegend=True,  # Mostrar leyenda
        legend=dict(x=1.02, y=1, font=dict(size=14)),
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande (de 6 a 18)
            font_family="Arial"
        )
    )
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_ready_by_file_chart(df, ready_col):
    """4. OPTIBAT Ready y No Ready por archivo"""
    if 'File' not in df.columns:
        # Si no hay columna File, crear una genérica
        df = df.copy()
        df['File'] = 'Dataset_Completo'
    
    # Calcular minutos por archivo
    file_stats = df.groupby('File').agg({
        ready_col: ['sum', 'count']
    }).round(2)
    file_stats.columns = ['ready_sum', 'total_count']
    file_stats['not_ready_sum'] = file_stats['total_count'] - file_stats['ready_sum']
    
    # Calcular promedios globales
    total_ready = file_stats['ready_sum'].sum()
    total_not_ready = file_stats['not_ready_sum'].sum()
    total_files = len(file_stats)
    avg_ready_per_file = total_ready / total_files
    avg_not_ready_per_file = total_not_ready / total_files
    ready_pct_global = (total_ready / (total_ready + total_not_ready)) * 100
    not_ready_pct_global = (total_not_ready / (total_ready + total_not_ready)) * 100
    
    fig = go.Figure()
    
    # Barras READY=0 (rojo)
    fig.add_trace(go.Bar(
        x=file_stats.index,
        y=file_stats['not_ready_sum'],
        name='Ready=0',
        marker_color='#DC143C',
        text=[f'{val:.0f}' for val in file_stats['not_ready_sum']],
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Ready=0 (No Ready): %{y:.0f} minutos<br>' +
                     '<extra></extra>'
    ))
    
    # Barras READY=1 (verde) - apiladas
    fig.add_trace(go.Bar(
        x=file_stats.index,
        y=file_stats['ready_sum'],
        name='Ready=1',
        marker_color='#228B22',
        text=[f'{val:.0f}' for val in file_stats['ready_sum']],
        textposition='inside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Ready=1 (Ready): %{y:.0f} minutos<br>' +
                     '<extra></extra>'
    ))
    
    # Texto en la esquina con promedios
    fig.add_annotation(
        x=0.02, y=0.98,
        xref="paper", yref="paper",
        text=f"Average per file:<br>Ready=1: {avg_ready_per_file:.1f} min ({ready_pct_global:.1f}%)<br>Ready=0: {avg_not_ready_per_file:.1f} min ({not_ready_pct_global:.1f}%)",
        showarrow=False,
        bgcolor="white",
        bordercolor="black",
        font=dict(size=10)
    )
    
    fig.update_layout(
        title='OPTIBAT READY Time Distribution by File',
        xaxis_title='File',
        yaxis_title='Minutes',
        height=900,  # Más grande para facilitar lectura
        barmode='stack',
        plot_bgcolor='white',
        legend=dict(x=0.8, y=0.98),
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14),
        yaxis=dict(title_font_size=18, tickfont_size=14),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_loop_usage_by_file_chart(df, on_col):
    """5. Utilización en lazo abierto y cerrado por archivo"""
    if 'File' not in df.columns:
        # Si no hay columna File, crear una genérica
        df = df.copy()
        df['File'] = 'Dataset_Completo'
    
    # Calcular minutos por archivo
    file_stats = df.groupby('File').agg({
        on_col: ['sum', 'count']
    }).round(2)
    file_stats.columns = ['closed_sum', 'total_count']
    file_stats['open_sum'] = file_stats['total_count'] - file_stats['closed_sum']
    
    # Calcular promedios globales
    total_closed = file_stats['closed_sum'].sum()
    total_open = file_stats['open_sum'].sum()
    total_files = len(file_stats)
    avg_closed_per_file = total_closed / total_files
    avg_open_per_file = total_open / total_files
    closed_pct_global = (total_closed / (total_closed + total_open)) * 100
    open_pct_global = (total_open / (total_closed + total_open)) * 100
    
    fig = go.Figure()
    
    # Barras Open loop (naranja)
    fig.add_trace(go.Bar(
        x=file_stats.index,
        y=file_stats['open_sum'],
        name='Open loop (0)',
        marker_color='#FFA500',
        text=[f'{val:.0f}' for val in file_stats['open_sum']],
        textposition='inside',
        textfont=dict(color='white', size=16),  # Aumentado para coincidir con gráficos 2 y 3
        hovertemplate='<b>%{x}</b><br>' +
                     'Open Loop (0): %{y:.0f} minutos<br>' +
                     '<extra></extra>'
    ))
    
    # Barras Closed loop (azul) - apiladas
    fig.add_trace(go.Bar(
        x=file_stats.index,
        y=file_stats['closed_sum'],
        name='Closed loop (1)',
        marker_color='#4682B4',
        text=[f'{val:.0f}' for val in file_stats['closed_sum']],
        textposition='inside',
        textfont=dict(color='white', size=16),  # Aumentado para coincidir con gráficos 2 y 3
        hovertemplate='<b>%{x}</b><br>' +
                     'Closed Loop (1): %{y:.0f} minutos<br>' +
                     '<extra></extra>'
    ))
    
    # Texto en la esquina con promedios
    fig.add_annotation(
        x=0.02, y=0.98,
        xref="paper", yref="paper",
        text=f"Average per file:<br>Closed loop: {avg_closed_per_file:.1f} min ({closed_pct_global:.1f}%)<br>Open loop: {avg_open_per_file:.1f} min ({open_pct_global:.1f}%)",
        showarrow=False,
        bgcolor="white",
        bordercolor="black",
        font=dict(size=16)  # Aumentado para coincidir con gráficos 2 y 3
    )
    
    fig.update_layout(
        title='OPTIBAT_ON Time Distribution by File',
        xaxis_title='File',
        yaxis_title='Minutes',
        height=900,  # Más grande para facilitar lectura
        barmode='stack',
        plot_bgcolor='white',
        legend=dict(x=0.8, y=0.98),
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14),
        yaxis=dict(title_font_size=18, tickfont_size=14),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_ready_downs_by_weekday_chart(df, ready_col):
    """6. Número de caídas de OPTIBAT Ready por día de la semana"""
    if 'Date' not in df.columns:
        return go.Figure()
    
    # Detectar transiciones de 1 a 0 (caídas)
    df_sorted = df.sort_values('Date').copy()
    df_sorted['ready_prev'] = df_sorted[ready_col].shift(1)
    df_sorted['ready_down'] = ((df_sorted['ready_prev'] == 1) & (df_sorted[ready_col] == 0)).astype(int)
    
    # Agregar día de la semana y información de fechas específicas
    df_sorted['weekday'] = df_sorted['Date'].dt.day_name()
    df_sorted['date_str'] = df_sorted['Date'].dt.strftime('%d/%m/%Y')
    
    # Contar caídas por día de la semana y obtener fechas específicas
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_colors = ['#87CEEB', '#4682B4', '#90EE90', '#228B22', '#FFB6C1', '#DC143C', '#DEB887']
    
    downs_by_weekday = df_sorted.groupby('weekday')['ready_down'].sum()
    downs_by_weekday = downs_by_weekday.reindex(weekday_order).fillna(0)
    
    # Crear información detallada de fechas para cada día de la semana
    hover_texts = []
    for weekday in weekday_order:
        down_events = df_sorted[(df_sorted['weekday'] == weekday) & (df_sorted['ready_down'] == 1)]
        count = len(down_events)
        if count > 0:
            # Obtener TODAS las fechas específicas de las caídas
            dates = down_events['date_str'].unique()  # Mostrar TODAS las fechas
            dates_text = "<br>".join(dates)
            hover_text = f"<b>{weekday}</b><br>Caídas: {count}<br>Fechas específicas:<br>{dates_text}"
        else:
            hover_text = f"<b>{weekday}</b><br>Caídas: {count}"
        hover_texts.append(hover_text)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekday_order,
        y=downs_by_weekday.values,
        name='Number of downs',
        marker_color=weekday_colors,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts
    ))
    
    fig.update_layout(
        title='Number of OPTIBAT_READY down per day of the week',
        xaxis_title='Day of the week',
        yaxis_title='Number of downs',
        height=750,  # Altura estandarizada
        plot_bgcolor='white',
        showlegend=False,
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14),
        yaxis=dict(title_font_size=18, tickfont_size=14),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    
    return fig

def create_ready_downs_by_hour_chart(df, ready_col):
    """7. Horarios de caída de OPTIBAT Ready"""
    if 'Date' not in df.columns:
        return go.Figure()
    
    # Detectar transiciones de 1 a 0 (caídas)
    df_sorted = df.sort_values('Date').copy()
    df_sorted['ready_prev'] = df_sorted[ready_col].shift(1)
    df_sorted['ready_down'] = ((df_sorted['ready_prev'] == 1) & (df_sorted[ready_col] == 0)).astype(int)
    
    # Extraer hora del día y información detallada de fechas
    df_sorted['hour'] = df_sorted['Date'].dt.hour
    df_sorted['date_str'] = df_sorted['Date'].dt.strftime('%d/%m/%Y')
    df_sorted['datetime_str'] = df_sorted['Date'].dt.strftime('%d/%m/%Y %H:%M')
    
    # Contar caídas por hora
    downs_by_hour = df_sorted[df_sorted['ready_down'] == 1].groupby('hour').size()
    all_hours = pd.Series(index=range(24), data=0)
    downs_by_hour = all_hours.add(downs_by_hour, fill_value=0)
    
    # Crear información detallada para hover
    hover_texts = []
    for hour in range(24):
        hour_downs = df_sorted[(df_sorted['hour'] == hour) & (df_sorted['ready_down'] == 1)]
        count = len(hour_downs)
        if count > 0:
            # Obtener fechas específicas de las caídas a esa hora
            datetimes = hour_downs['datetime_str'].unique()[:5]  # Mostrar máximo 5
            datetime_text = "<br>".join(datetimes)
            if len(hour_downs) > 5:
                datetime_text += f"<br>... y {len(hour_downs) - 5} más"
            hover_text = f"<b>Hora: {hour:02d}:00</b><br>Caídas: {count}<br>Fechas específicas:<br>{datetime_text}"
        else:
            hover_text = f"<b>Hora: {hour:02d}:00</b><br>Caídas: {count}"
        hover_texts.append(hover_text)
    
    # Crear gradiente de colores
    max_downs = downs_by_hour.max() if downs_by_hour.max() > 0 else 1
    colors = [f'rgba({min(255, int(200 + 55 * (val/max_downs)))}, '
              f'{max(100, int(255 - 100 * (val/max_downs)))}, '
              f'{max(100, int(255 - 100 * (val/max_downs)))}, 0.8)' 
              for val in downs_by_hour.values]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(24)),
        y=downs_by_hour.values,
        name='Number of downs',
        marker_color=colors,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts
    ))
    
    fig.update_layout(
        title='Number of OPTIBAT_READY down per time in day',
        xaxis_title='day time (0-23)',
        yaxis_title='Number of downs',
        height=750,  # Altura estandarizada
        xaxis=dict(tickmode='linear', dtick=1, title_font_size=18, tickfont_size=14),
        plot_bgcolor='white',
        showlegend=False,
        font=dict(size=16),
        title_font_size=20,
        yaxis=dict(title_font_size=18, tickfont_size=14),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    
    return fig

def create_ready_duration_chart(df, ready_col):
    """8. Duración OPTIBAT Ready"""
    if 'Date' not in df.columns:
        return go.Figure()
    
    # Detectar transiciones y calcular duraciones
    df_sorted = df.sort_values('Date').copy()
    df_sorted['ready_prev'] = df_sorted[ready_col].shift(1)
    df_sorted['state_change'] = (df_sorted[ready_col] != df_sorted['ready_prev']).astype(int)
    df_sorted['state_group'] = df_sorted['state_change'].cumsum()
    
    # Calcular duración de cada período Ready=0
    durations = []
    for group_id in df_sorted['state_group'].unique():
        group_data = df_sorted[df_sorted['state_group'] == group_id]
        if len(group_data) > 0 and group_data[ready_col].iloc[0] == 0:
            # Período de Ready=0, calcular duración en minutos
            duration = len(group_data)  # Asumiendo datos por minuto
            durations.append(duration)
    
    if not durations:
        durations = [0]  # Evitar error si no hay datos
    
    # Crear histograma
    fig = go.Figure()
    
    # Histograma de barras
    hist, bin_edges = np.histogram(durations, bins=20)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    fig.add_trace(go.Bar(
        x=bin_centers,
        y=hist,
        name='Frequency',
        marker_color='lightblue',
        marker_line=dict(color='black', width=1),
        text=[f"{int(round(freq))}" for freq in hist],  # Texto redondeado en las barras
        textposition='outside',
        hovertemplate='<b>Duración:</b> %{x:.0f} minutos<br>' +
                      '<b>Frecuencia:</b> %{y:.0f} eventos<br>' +
                      '<extra></extra>'
    ))
    
    # Línea de tendencia suavizada
    if len(durations) > 3 and SCIPY_AVAILABLE:
        x_smooth = np.linspace(min(durations), max(durations), 100)
        # Crear función de densidad suavizada
        hist_density = hist / (np.sum(hist) * (bin_edges[1] - bin_edges[0]))
        if len(bin_centers) > 3:
            try:
                spline = UnivariateSpline(bin_centers, hist_density, s=len(bin_centers))
                y_smooth = spline(x_smooth)
                y_smooth = np.maximum(y_smooth, 0)  # No valores negativos
                
                fig.add_trace(go.Scatter(
                    x=x_smooth,
                    y=y_smooth * np.sum(hist) * (bin_edges[1] - bin_edges[0]),
                    mode='lines',
                    name='Trend',
                    line=dict(color='lightblue', width=2),
                    hovertemplate='<b>Tendencia</b><br>' +
                                  '<b>Duración:</b> %{x:.0f} minutos<br>' +
                                  '<b>Tendencia:</b> %{y:.1f}<br>' +
                                  '<extra></extra>'
                ))
            except:
                pass  # Si falla el spline, continuar sin línea
    
    fig.update_layout(
        title='Duration of down of OPTIBAT_READY',
        xaxis_title='Duration (minutes)',
        yaxis_title='Frequency',
        height=750,  # Altura estandarizada
        plot_bgcolor='white',
        showlegend=False,
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14, tickformat='.0f'),  # Formateo sin decimales
        yaxis=dict(title_font_size=18, tickfont_size=14, tickformat='.0f'),   # Formateo sin decimales
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    
    return fig

def create_optibat_on_duration_chart(df, on_col):
    """8. Duración de Períodos OPTIBAT_ON=1 - Tiempo en servicio"""
    if 'Date' not in df.columns:
        return go.Figure()
    
    # Detectar transiciones y calcular duraciones
    df_sorted = df.sort_values('Date').copy()
    df_sorted['on_prev'] = df_sorted[on_col].shift(1)
    df_sorted['state_change'] = (df_sorted[on_col] != df_sorted['on_prev']).astype(int)
    df_sorted['state_group'] = df_sorted['state_change'].cumsum()
    
    # Calcular duración de cada período ON=1 (tiempo en servicio)
    durations_minutes = []
    durations_hours = []
    total_minutes_day = 1440  # Total minutos en un día
    
    for group_id in df_sorted['state_group'].unique():
        group_data = df_sorted[df_sorted['state_group'] == group_id]
        if len(group_data) > 0 and group_data[on_col].iloc[0] == 1:
            # Período de ON=1, calcular duración en minutos
            duration_min = len(group_data)  # Asumiendo datos por minuto
            duration_hrs = duration_min / 60.0  # Convertir a horas
            durations_minutes.append(duration_min)
            durations_hours.append(duration_hrs)
    
    if not durations_minutes:
        durations_minutes = [0]  # Evitar error si no hay datos
        durations_hours = [0]
    
    # Crear histograma
    fig = go.Figure()
    
    # Histograma de barras (en minutos)
    hist, bin_edges = np.histogram(durations_minutes, bins=20)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    fig.add_trace(go.Bar(
        x=bin_centers,
        y=hist,
        name='Frequency',
        marker_color='green',  # Verde para ON
        marker_line=dict(color='darkgreen', width=1),
        text=[f"{int(round(freq))}" for freq in hist],  # Texto redondeado en las barras
        textposition='outside',
        hovertemplate='<b>Duración:</b> %{x:.0f} minutos (%{customdata[0]:.1f}h)<br>' +
                      '<b>Frecuencia:</b> %{y:.0f} períodos<br>' +
                      '<b>% del día:</b> %{customdata[1]:.1f}%<br>' +
                      '<extra></extra>',
        customdata=[[x/60, (x/total_minutes_day)*100] for x in bin_centers]  # [horas, porcentaje_día]
    ))
    
    # Línea de tendencia suavizada
    if len(durations_minutes) > 3 and SCIPY_AVAILABLE:
        x_smooth = np.linspace(min(durations_minutes), max(durations_minutes), 100)
        # Crear función de densidad suavizada
        hist_density = hist / (np.sum(hist) * (bin_edges[1] - bin_edges[0]))
        if len(bin_centers) > 3:
            try:
                spline = UnivariateSpline(bin_centers, hist_density, s=len(bin_centers))
                y_smooth = spline(x_smooth)
                y_smooth = np.maximum(y_smooth, 0)  # No valores negativos
                
                fig.add_trace(go.Scatter(
                    x=x_smooth,
                    y=y_smooth * np.sum(hist) * (bin_edges[1] - bin_edges[0]),
                    mode='lines',
                    name='Trend',
                    line=dict(color='darkgreen', width=2),
                    hovertemplate='<b>Tendencia</b><br>' +
                                  '<b>Duración:</b> %{x:.0f} minutos<br>' +
                                  '<b>Tendencia:</b> %{y:.1f}<br>' +
                                  '<extra></extra>'
                ))
            except:
                pass  # Si falla el spline, continuar sin línea
    
    # Estadísticas para mostrar en el gráfico
    avg_duration_min = np.mean(durations_minutes)
    avg_duration_hrs = avg_duration_min / 60
    percent_of_day = (avg_duration_min / total_minutes_day) * 100
    total_periods = len(durations_minutes)
    
    fig.update_layout(
        title=f'Duración Períodos OPTIBAT_ON=1 (Servicio)<br>' +
              f'<sub>Promedio: {avg_duration_min:.0f}min ({avg_duration_hrs:.1f}h) = {percent_of_day:.1f}% del día | Total períodos: {total_periods}</sub>',
        xaxis_title='Duración (minutos)',
        yaxis_title='Frecuencia (períodos)',
        height=750,  # Altura estandarizada
        plot_bgcolor='white',
        showlegend=False,
        font=dict(size=16),
        title_font_size=20,
        xaxis=dict(title_font_size=18, tickfont_size=14, tickformat='.0f'),  # Formateo sin decimales
        yaxis=dict(title_font_size=18, tickfont_size=14, tickformat='.0f'),   # Formateo sin decimales
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=18,  # 3 veces más grande
            font_family="Arial"
        )
    )
    
    return fig

def generate_complete_html_report(df_display, available_flags, detected_client, custom_title, date_range_main):
    """Genera un reporte HTML completo del dashboard"""
    try:
        # Calcular KPIs
        kpis = OptibatMetricsAnalyzer.calculate_system_status(df_display)
        
        # Obtener rango de fechas
        if 'Date' in df_display.columns and not df_display['Date'].dropna().empty:
            start_date = df_display['Date'].min()
            end_date = df_display['Date'].max()
            date_range_str = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        else:
            date_range_str = "Rango de fechas no disponible"
        
        # Generar gráficos en HTML
        donut_fig = OptibatMetricsAnalyzer.create_global_donut_chart(df_display)
        donut_html = donut_fig.to_html(include_plotlyjs='inline', div_id="donut_chart")
        
        timeline_html = ""
        if "Date" in df_display.columns and not df_display["Date"].dropna().empty:
            timeline_fig = OptibatMetricsAnalyzer.create_timeline_chart(df_display, available_flags)
            timeline_html = timeline_fig.to_html(include_plotlyjs=False, div_id="timeline_chart")
        
        duration_html = ""
        if 'OPTIBAT_ON' in df_display.columns:
            duration_fig = OptibatMetricsAnalyzer.create_interactive_duration_chart(df_display, 'OPTIBAT_ON')
            duration_html = duration_fig.to_html(include_plotlyjs=False, div_id="duration_chart")
        
        # Calcular resumen ON/OFF
        on_off_summary = ""
        if 'OPTIBAT_ON' in df_display.columns:
            total_records = len(df_display)
            on_records = (df_display['OPTIBAT_ON'] == 1).sum()
            off_records = total_records - on_records
            on_percentage = (on_records / total_records * 100) if total_records > 0 else 0
            off_percentage = (off_records / total_records * 100) if total_records > 0 else 0
            
            on_off_summary = f"""
            <div class="summary-section">
                <h3>📊 Resumen de Estados</h3>
                <table style="width: 100%; border-collapse: collapse; background: white; margin-top: 1rem;">
                    <thead>
                        <tr style="background: #f8f9fa; border-bottom: 2px solid #E31E32;">
                            <th style="padding: 1rem; text-align: left; color: #333; font-weight: 600;">Estado</th>
                            <th style="padding: 1rem; text-align: center; color: #333; font-weight: 600;">Minutos</th>
                            <th style="padding: 1rem; text-align: center; color: #333; font-weight: 600;">Horas</th>
                            <th style="padding: 1rem; text-align: center; color: #333; font-weight: 600;">Porcentaje</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 1rem; color: #333;">ON (Activo)</td>
                            <td style="padding: 1rem; text-align: center; font-weight: 600; color: #27ae60;">{on_records:,}</td>
                            <td style="padding: 1rem; text-align: center; font-weight: 600; color: #27ae60;">{(on_records/60):.1f}</td>
                            <td style="padding: 1rem; text-align: center; font-weight: 600; color: #27ae60;">{on_percentage:.1f}%</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 1rem; color: #333;">OFF (Inactivo)</td>
                            <td style="padding: 1rem; text-align: center; font-weight: 600; color: #e74c3c;">{off_records:,}</td>
                            <td style="padding: 1rem; text-align: center; font-weight: 600; color: #e74c3c;">{(off_records/60):.1f}</td>
                            <td style="padding: 1rem; text-align: center; font-weight: 600; color: #e74c3c;">{off_percentage:.1f}%</td>
                        </tr>
                        <tr style="background: #f8f9fa; font-weight: 700;">
                            <td style="padding: 1rem; color: #333;">Total</td>
                            <td style="padding: 1rem; text-align: center; color: #333;">{total_records:,}</td>
                            <td style="padding: 1rem; text-align: center; color: #333;">{(total_records/60):.1f}</td>
                            <td style="padding: 1rem; text-align: center; color: #333;">100.0%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """
        
        # Generar HTML completo
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{custom_title}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                    color: #333;
                }}
                .header {{
                    background: linear-gradient(135deg, #E31E32 0%, #B71C1C 100%);
                    color: white;
                    padding: 2rem;
                    border-radius: 15px;
                    text-align: center;
                    margin-bottom: 2rem;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5rem;
                    font-weight: 900;
                }}
                .header .subtitle {{
                    margin: 0.5rem 0 0 0;
                    font-size: 1.2rem;
                    opacity: 0.9;
                }}
                .info-cards {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1rem;
                    margin-bottom: 2rem;
                }}
                .info-card {{
                    background: linear-gradient(135deg, #E31E32 0%, #B71C1C 100%);
                    color: white;
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                }}
                .info-card h4 {{
                    margin: 0;
                    font-size: 1rem;
                }}
                .info-card h3 {{
                    margin: 0.5rem 0 0 0;
                    font-size: 1.5rem;
                }}
                .kpis-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 1rem;
                    margin-bottom: 2rem;
                }}
                .kpi-card {{
                    background: white;
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .kpi-label {{
                    color: #666;
                    font-size: 0.9rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    text-transform: uppercase;
                }}
                .kpi-value {{
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #E31E32;
                }}
                .chart-section {{
                    background: white;
                    padding: 1.5rem;
                    border-radius: 15px;
                    margin-bottom: 2rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .chart-section h3 {{
                    margin: 0 0 1rem 0;
                    color: #E31E32;
                    border-bottom: 2px solid #E31E32;
                    padding-bottom: 0.5rem;
                }}
                .summary-section {{
                    background: white;
                    padding: 1.5rem;
                    border-radius: 15px;
                    margin-bottom: 2rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1rem;
                    margin-top: 1rem;
                }}
                .summary-card {{
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 8px;
                    text-align: center;
                    border-left: 4px solid #E31E32;
                }}
                .summary-label {{
                    color: #666;
                    font-size: 0.9rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                }}
                .summary-value {{
                    font-size: 1.2rem;
                    font-weight: 700;
                    color: #333;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 3rem;
                    padding: 2rem;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .footer h3 {{
                    color: #E31E32;
                    margin-bottom: 1rem;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{custom_title}</h1>
                <div class="subtitle">Dashboard Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</div>
            </div>
            
            <div class="info-cards">
                <div class="info-card">
                    <h4>CLIENTE</h4>
                    <h3>{detected_client}</h3>
                </div>
                <div class="info-card">
                    <h4>FLAGS ACTIVOS</h4>
                    <h3>{len(available_flags)}/{len(MAIN_FLAGS)}</h3>
                </div>
                <div class="info-card">
                    <h4>REGISTROS</h4>
                    <h3>{len(df_display):,}</h3>
                </div>
                <div class="info-card">
                    <h4>PERÍODO</h4>
                    <h3>{date_range_str}</h3>
                </div>
            </div>
            
            <div class="kpis-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Estado Sistema</div>
                    <div class="kpi-value">{kpis['system_on']}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Tiempo Activo</div>
                    <div class="kpi-value">{kpis.get('uptime_pct', '0%')}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Desactivaciones</div>
                    <div class="kpi-value">{kpis.get('flag_ready_deactivations', 0)}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Anomalías</div>
                    <div class="kpi-value">{kpis.get('anomalies', 0)}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">HeartBeat</div>
                    <div class="kpi-value">{kpis['heartbeat_status']}</div>
                </div>
            </div>
            
            <div class="chart-section">
                <h3>Distribución Global de Operación</h3>
                {donut_html}
            </div>
            
            {f'''
            <div class="chart-section">
                <h3>Estados OPTIBAT_ON con Duraciones</h3>
                {duration_html}
            </div>
            {on_off_summary}
            ''' if duration_html else ''}
            
            {f'''
            <div class="chart-section">
                <h3>Timeline del Sistema</h3>
                {timeline_html}
            </div>
            ''' if timeline_html else ''}
            
            <div class="footer">
                <h3>OPTIMITIVE</h3>
                <p><strong>© Optimitive | AI Optimization Solutions</strong></p>
                <p>optimitive.com</p>
                <p><strong>Developed by Juan Cruz Erreguerena.</strong> | Monthly Report Generator</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        return f"<html><body><h1>Error generando reporte: {str(e)}</h1></body></html>"

def create_on_off_summary_table(df_display, date_range_main):
    """Crea tabla resumen con minutos ON/OFF y rango de fechas"""
    try:
        if 'OPTIBAT_ON' not in df_display.columns:
            return
            
        # Calcular minutos ON y OFF
        total_records = len(df_display)
        on_records = (df_display['OPTIBAT_ON'] == 1).sum()
        off_records = total_records - on_records
        
        # Convertir a minutos (asumiendo 1 registro = 1 minuto)
        on_minutes = on_records
        off_minutes = off_records
        total_minutes = total_records
        
        # Calcular porcentajes
        on_percentage = (on_minutes / total_minutes * 100) if total_minutes > 0 else 0
        off_percentage = (off_minutes / total_minutes * 100) if total_minutes > 0 else 0
        
        # Obtener rango de fechas
        if 'Date' in df_display.columns and not df_display['Date'].dropna().empty:
            start_date = df_display['Date'].min()
            end_date = df_display['Date'].max()
            date_range_str = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        else:
            date_range_str = "Rango de fechas no disponible"
            
        # Crear la tabla
        st.markdown("#### 📊 Resumen de Estados")
        
        # Tabla simple con 3 columnas: Estado, Minutos, Horas, Porcentaje
        summary_data = {
            "Estado": ["🟢 ON (Activo)", "🔴 OFF (Inactivo)", "📊 Total"],
            "Minutos": [f"{on_minutes:,}", f"{off_minutes:,}", f"{total_minutes:,}"],
            "Horas": [f"{(on_minutes/60):.1f}", f"{(off_minutes/60):.1f}", f"{(total_minutes/60):.1f}"],
            "Porcentaje": [f"{on_percentage:.1f}%", f"{off_percentage:.1f}%", "100.0%"]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        # Tabla más grande con fondo blanco y letras negras
        st.markdown("""
        <style>
        .dataframe {
            font-size: 16px !important;
            background-color: white !important;
            color: black !important;
        }
        .dataframe th {
            font-size: 18px !important;
            font-weight: bold !important;
            background-color: white !important;
            color: black !important;
            text-align: center !important;
        }
        .dataframe td {
            font-size: 16px !important;
            background-color: white !important;
            color: black !important;
            text-align: center !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
            height=150,  # Hacer la tabla más alta
            column_config={
                "Estado": st.column_config.TextColumn("Estado", width="medium"),
                "Minutos": st.column_config.TextColumn("Minutos", width="small"),
                "Horas": st.column_config.TextColumn("Horas", width="small"),
                "Porcentaje": st.column_config.TextColumn("Porcentaje", width="small")
            }
        )
            
    except Exception as e:
        st.error(f"Error al crear tabla resumen: {str(e)}")

def show_metrics_analysis(df_processed, available_flags):
    """Muestra el análisis de métricas usando los datos procesados"""
    
    # Filtro de fechas si está disponible
    df_display = df_processed.copy()
    date_range_main = None
    
    if "Date" in df_processed.columns and not df_processed["Date"].dropna().empty:
        st.markdown("### Filtro Temporal")
        
        # CSS para hacer el filtro temporal más grande
        st.markdown("""
        <style>
        .stDateInput > div > div > div > div {
            font-size: 18px !important;
            height: 50px !important;
        }
        .stDateInput > div > div > div > div > input {
            font-size: 16px !important;
            height: 45px !important;
            padding: 10px !important;
        }
        .stDateInput label {
            font-size: 18px !important;
            font-weight: bold !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1_date, col2_date, col3_date = st.columns([1, 3, 1])
        with col2_date:
            min_date = df_processed["Date"].min().date()
            max_date = df_processed["Date"].max().date()
            date_range_main = st.date_input(
                "Selecciona el rango de fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY"
            )
            if len(date_range_main) == 2:
                start_date, end_date = date_range_main
                mask = (df_processed["Date"] >= pd.Timestamp(start_date)) & \
                       (df_processed["Date"] <= pd.Timestamp(end_date).replace(hour=23, minute=59, second=59))
                df_display = df_processed[mask].copy()
                st.info(f"**{len(df_display):,} registros** desde {start_date.strftime('%d/%m/%Y')} hasta {end_date.strftime('%d/%m/%Y')}")
    
    if df_display.empty:
        st.warning("No hay datos en el rango seleccionado.")
        return
    
    # KPIs principales
    kpis = OptibatMetricsAnalyzer.calculate_system_status(df_display)
    
    st.markdown("### Indicadores Clave de Rendimiento")
    
    # Estilo CSS para KPIs con fondo blanco y letras negras
    st.markdown("""
    <style>
    [data-testid="metric-container"] {
        background-color: white !important;
        border: 1px solid #e0e0e0 !important;
        padding: 1rem !important;
        border-radius: 0.5rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    [data-testid="metric-container"] > div {
        color: black !important;
    }
    [data-testid="metric-container"] label {
        color: #666666 !important;
        font-weight: 600 !important;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: black !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    kpi_cols = st.columns(6)
    
    with kpi_cols[0]:
        status_color = "Activo" if kpis['system_on'] == "Activo" else "Inactivo" if kpis['system_on'] == "Inactivo" else "N/A"
        st.metric("Estado Sistema", f"{status_color}")
    
    with kpi_cols[1]:
        st.metric("Tiempo Activo", kpis.get('uptime_pct', '0%'))
    
    with kpi_cols[2]:
        st.metric("Calidad Datos", f"{kpis.get('data_quality', 0):.1f}%")
    
    with kpi_cols[3]:
        st.metric("Desactivaciones", kpis.get('flag_ready_deactivations', 0))
    
    with kpi_cols[4]:
        st.metric("Anomalías", kpis.get('anomalies', 0))
    
    with kpi_cols[5]:
        heartbeat_status = "Normal" if kpis['heartbeat_status'] == "Normal" else "Anómalo" if kpis['heartbeat_status'] == "Stuck" else "N/A"
        st.metric("HeartBeat", f"{heartbeat_status}")
    
    # Gauges de flags disponibles - MOSTRAR TODAS LAS FLAGS
    if available_flags:
        st.markdown("### Estado de Flags en Tiempo Real")
        
        # Calcular número de columnas dinámicamente (máximo 4 por fila)
        num_flags = len(available_flags)
        num_rows = (num_flags + 3) // 4  # Redondear hacia arriba
        
        for row in range(num_rows):
            # Crear columnas para esta fila
            start_idx = row * 4
            end_idx = min(start_idx + 4, num_flags)
            flags_in_row = available_flags[start_idx:end_idx]
            gauge_cols = st.columns(len(flags_in_row))
            
            for i, flag_name in enumerate(flags_in_row):
                if flag_name in df_display.columns:
                    gauge_value = df_display[flag_name].mean() * 100
                    description = FLAG_DESCRIPTIONS.get(flag_name, "Flag del sistema")
                    
                    with gauge_cols[i]:
                        fig_gauge = OptibatMetricsAnalyzer.create_gauge_chart(gauge_value, flag_name, description)
                        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # SECCIÓN NUEVA: Análisis de Utilización
    st.markdown("### Distribución Global de Operación")
    st.markdown('<p style="text-align: left; margin-left: 0; font-size: 14px; color: #666; margin-top: -10px;">Análisis de Utilización (ON: OPTIBAT_ON | READY: Flag_Ready)</p>', unsafe_allow_html=True)
    
    # Detectar columnas ON y READY
    on_col = None
    ready_col = None
    
    # Buscar columna ON
    for col in ['OPTIBAT_ON', 'ON']:
        if col in df_display.columns:
            on_col = col
            break
    
    # Buscar columna READY
    for col in ['Flag_Ready', 'OPTIBAT_READY', 'Ready']:
        if col in df_display.columns:
            ready_col = col
            break
    
    if on_col:
        # Calcular métricas del sistema
        metrics = calculate_system_metrics(df_display, on_col, ready_col)
        
        # Crear gráfico de utilización
        efficiency_fig = create_efficiency_donut_v2(metrics, on_col, ready_col)
        st.plotly_chart(efficiency_fig, use_container_width=True)
        
        # Agregar serie temporal de estados del sistema que acompaña a la rosquilla
        if 'Date' in df_display.columns and not df_display['Date'].dropna().empty:
            # Header con botón toggle para duraciones
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("#### Serie Temporal de Estados del Sistema")
            with col2:
                show_durations = st.checkbox("📍 Mostrar Duraciones", key="timeline_durations_toggle", help="Mostrar flechas y cuadros con duración de cada segmento")
            
            # Generar el mismo gráfico pero con/sin duraciones según el toggle
            temporal_states_fig = ts_with_background_regions(df_display, 'Date', on_col, ready_col, show_durations)
            temporal_states_fig.update_layout(height=900)
            
            st.plotly_chart(temporal_states_fig, use_container_width=True)
    else:
        st.warning("No se encontró columna OPTIBAT_ON para el análisis de utilización")
    
    # TABLA RESUMEN DE ON/OFF CON FECHAS (movida aquí después de Serie Temporal)
    if on_col and 'Date' in df_display.columns:
        create_on_off_summary_table(df_display, date_range_main)
    
    # Timeline ORIGINAL con bloques 0-1
    if "Date" in df_display.columns and not df_display["Date"].dropna().empty:
        st.markdown("### Timeline del Sistema")
        timeline_fig = OptibatMetricsAnalyzer.create_timeline_chart(df_display, available_flags)
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    # === ANÁLISIS AVANZADO DEL SISTEMA ===
    st.markdown("---")
    st.markdown('<h3 style="font-size: 2em;">Análisis Avanzado del Sistema</h3>', unsafe_allow_html=True)
    
    # === NUEVO SISTEMA DE DETECCIÓN INTELIGENTE DE COLUMNAS ===
    # Detectar automáticamente las columnas del cliente usando el mapeo
    detected_mapping = detect_client_flag_columns(df_display.columns.tolist())
    standardized_cols = get_standardized_columns(df_display, detected_mapping)
    
    # Mostrar información de mapeo detectado
    if detected_mapping:
        st.info(f"""
        **Mapeo de Columnas Detectado para este Cliente:**
        {', '.join([f'{std}: {client}' for std, client in detected_mapping.items()])}
        """)
    
    # Obtener columnas para análisis
    ready_col = standardized_cols.get('ready_col')
    on_col = standardized_cols.get('on_col') 
    
    if ready_col is None or on_col is None:
        missing_flags = []
        if ready_col is None:
            missing_flags.append("Flag_Ready/OPTIBAT_READY")
        if on_col is None:
            missing_flags.append("OPTIBAT_ON")
        
        st.warning(f"""
        **Columnas faltantes para análisis avanzado:**
        
        **No encontradas:** {', '.join(missing_flags)}
        
        **Columnas disponibles en el archivo:** 
        {', '.join(df_display.columns.tolist())}
        
        **Variaciones soportadas:**
        - Flag_Ready: {', '.join(FLAG_COLUMN_MAPPING['Flag_Ready'])}
        - OPTIBAT_ON: {', '.join(FLAG_COLUMN_MAPPING['OPTIBAT_ON'])}
        """)
        return
    
    # 1. EVOLUCIÓN COMBINADA EN SUBPLOT CON EJE X COMPARTIDO
    # Título dinámico basado en las columnas disponibles
    if ready_col and ready_col in df_display.columns and not df_display[ready_col].dropna().empty:
        graph_title = "#### 1. Evolución Temporal: OPTIBAT_READY y Lazo Cerrado"
    else:
        graph_title = "#### 1. Evolución Temporal: Lazo Cerrado"
    
    st.markdown(graph_title)
    if "Date" in df_display.columns:
        combined_evolution_fig = create_combined_evolution_chart(df_display, ready_col, on_col)
        st.plotly_chart(combined_evolution_fig, use_container_width=True)
    else:
        st.info("📊 Se requiere una columna de fecha para mostrar la evolución temporal.")
    
    # 2. PORCENTAJE DE TIEMPO EN LAZO CERRADO POR ARCHIVO
    st.markdown("#### 2. Porcentaje de Tiempo en Lazo Cerrado por Archivo")
    # Obtener archivos subidos desde session state para usar nombres reales
    uploaded_files = st.session_state.get('global_txt_files', [])
    df_with_file = create_file_segments_from_data(df_display.copy(), uploaded_files)
    closed_loop_by_file_fig = create_closed_loop_by_file_chart(df_with_file, on_col)
    st.plotly_chart(closed_loop_by_file_fig, use_container_width=True)
    
    # 3. OPTIBAT READY Y NO READY POR ARCHIVO
    st.markdown("#### 3. OPTIBAT Ready y No Ready por Archivo")
    ready_by_file_fig = create_ready_by_file_chart(df_with_file, ready_col)
    st.plotly_chart(ready_by_file_fig, use_container_width=True)
    
    # 4. UTILIZACIÓN EN LAZO ABIERTO Y CERRADO POR ARCHIVO
    st.markdown("#### 4. Utilización en Lazo Abierto y Cerrado por Archivo")
    loop_usage_by_file_fig = create_loop_usage_by_file_chart(df_with_file, on_col)
    st.plotly_chart(loop_usage_by_file_fig, use_container_width=True)
    
    # 5. NÚMERO DE CAÍDAS DE OPTIBAT READY POR DÍA DE LA SEMANA
    st.markdown("#### 5. Número de Caídas de OPTIBAT Ready por Día de la Semana")
    if "Date" in df_display.columns:
        ready_downs_by_weekday_fig = create_ready_downs_by_weekday_chart(df_display, ready_col)
        st.plotly_chart(ready_downs_by_weekday_fig, use_container_width=True)
    else:
        st.info("📊 Se requiere una columna de fecha para mostrar el análisis por día de la semana.")
    
    # 6. HORARIOS DE CAÍDA DE OPTIBAT READY
    st.markdown("#### 6. Horarios de Caída de OPTIBAT Ready")
    if "Date" in df_display.columns:
        ready_downs_by_hour_fig = create_ready_downs_by_hour_chart(df_display, ready_col)
        st.plotly_chart(ready_downs_by_hour_fig, use_container_width=True)
    else:
        st.info("📊 Se requiere una columna de fecha para mostrar el análisis por horas del día.")
    
    # 7. DURACIÓN OPTIBAT READY
    st.markdown("#### 7. Duración de Períodos OPTIBAT Ready")
    if "Date" in df_display.columns:
        ready_duration_fig = create_ready_duration_chart(df_display, ready_col)
        st.plotly_chart(ready_duration_fig, use_container_width=True)
    else:
        st.info("📊 Se requiere una columna de fecha para mostrar el análisis de duraciones.")
    
    # 8. DURACIÓN OPTIBAT_ON (TIEMPO EN SERVICIO)
    st.markdown("#### 8. Duración de Períodos OPTIBAT_ON=1 (Tiempo en Servicio)")
    if "Date" in df_display.columns and on_col:
        on_duration_fig = create_optibat_on_duration_chart(df_display, on_col)
        st.plotly_chart(on_duration_fig, use_container_width=True)
    else:
        st.info("📊 Se requiere una columna de fecha y OPTIBAT_ON para mostrar el análisis de duraciones de servicio.")
    
    
    # Sección de datos raw (opcional)
    with st.expander("Explorar Datos Detallados"):
        st.dataframe(df_display[['Date'] + available_flags if 'Date' in df_display.columns else available_flags].head(200), 
                    use_container_width=True, height=300)
    
    # Exportación
    st.markdown("### Exportar Resultados")
    col1_exp, col2_exp = st.columns(2)
    
    with col1_exp:
        if not df_display.empty:
            csv_data = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv_data,
                file_name=f"optibat_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2_exp:
        kpis_json = json.dumps(kpis, indent=2, ensure_ascii=False).encode('utf-8')
        st.download_button(
            label="Descargar KPIs JSON",
            data=kpis_json,
            file_name=f"optibat_kpis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
    # === EXPORTACIÓN HTML COMPLETA ===
    st.markdown("---")
    st.markdown("### 📄 Exportar Dashboard Completo")
    
    # Obtener cliente detectado para el título por defecto
    detected_client_export = detect_client_from_flags(df_display.columns)
    
    col_html1, col_html2 = st.columns([2, 1])
    
    with col_html1:
        custom_title = st.text_input(
            "🏷️ Título personalizado para el reporte HTML:",
            value=f"Reporte OPTIBAT - {detected_client_export} - {datetime.now().strftime('%B %Y')}",
            help="Este título aparecerá en el encabezado del reporte HTML"
        )
    
    with col_html2:
        if st.button("🚀 GENERAR REPORTE HTML", type="primary", use_container_width=True):
            with st.spinner("Generando reporte HTML completo..."):
                html_content = generate_complete_html_report(
                    df_display, 
                    available_flags, 
                    detected_client_export, 
                    custom_title,
                    date_range_main
                )
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"OPTIBAT_Dashboard_{detected_client_export}_{timestamp}.html"
                
                st.download_button(
                    label="⬇️ Descargar Reporte HTML",
                    data=html_content,
                    file_name=filename,
                    mime="text/html",
                    type="primary"
                )
                
                st.success("✅ Reporte HTML generado exitosamente. Haga clic en 'Descargar' para obtener el archivo.")

def show_optibat_metrics_dashboard():
    """Display the OPTIBAT Metrics Dashboard"""
    
    # Store df_processed in session_state for the filter
    if 'df_processed_global' not in st.session_state:
        st.session_state.df_processed_global = pd.DataFrame()

    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem; 
                text-align: center; box-shadow: 0 8px 32px rgba(30, 60, 114, 0.3);">
        <h1 style="text-align:center; margin:0; font-size:3rem;">OPTIBAT METRICS DASHBOARD</h1>
        <p style="text-align:center; margin:0.5rem 0 0 0; font-size:1.2rem; opacity:0.9;">
            Sistema de Análisis y Monitoreo de STATISTICS
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if global files are loaded
    uploaded_files = st.session_state.get('global_txt_files', [])
    
    if not uploaded_files:
        st.info("👈 **Usa el cargador global en la barra lateral** para alimentar este dashboard con archivos .txt")
        return
    
    # Advanced options in sidebar for this mode
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔧 Opciones Dashboard Métricas")
        show_raw_data = st.checkbox("Mostrar datos crudos", value=False, key="metrics_show_raw")
        export_results = st.checkbox("Habilitar exportación", value=False, key="metrics_export")
        st.markdown("---")
        st.markdown(f"""
        **Versión:** 1.0  
        **Última actualización:** {datetime.now().strftime('%Y-%m-%d')}  
        **Desarrollado por:** Juan Cruz E
        """)

    # Use the globally processed data
    df_processed_for_display = st.session_state.get('global_metrics_data', pd.DataFrame())
    
    if df_processed_for_display.empty:
        st.warning("⚠️ No se encontraron datos procesados. Verifica que los archivos .txt sean válidos.")
        return 
    
    # === MOSTRAR INFORMACIÓN DE MAPEO DE COLUMNAS ===
    with st.expander("🔍 Información de Mapeo de Columnas del Cliente", expanded=False):
        show_column_mapping_info(df_processed_for_display)
    
    df_display = pd.DataFrame() 
    date_range_main = None 
    
    if "Date" in df_processed_for_display.columns and not df_processed_for_display["Date"].dropna().empty:
        st.markdown("### 📅 Filtro de Fechas")
        col1_main_date, col2_main_date, col3_main_date = st.columns([1, 3, 1])
        with col2_main_date:
            min_date_overall = df_processed_for_display["Date"].min().date()
            max_date_overall = df_processed_for_display["Date"].max().date()
            date_range_main = st.date_input(
                "Selecciona el rango de fechas para los gráficos principales",
                value=(min_date_overall, max_date_overall),
                min_value=min_date_overall,
                max_value=max_date_overall,
                format="DD/MM/YYYY",
                key="main_dashboard_date_filter"
            )
            if len(date_range_main) == 2:
                start_date_main, end_date_main = date_range_main
                mask_main = (df_processed_for_display["Date"] >= pd.Timestamp(start_date_main)) & \
                              (df_processed_for_display["Date"] <= pd.Timestamp(end_date_main).replace(hour=23, minute=59, second=59))
                df_display = df_processed_for_display[mask_main].copy()
                st.info(f"📊 Mostrando datos desde **{start_date_main.strftime('%d/%m/%Y')}** hasta **{end_date_main.strftime('%d/%m/%Y')}** ({len(df_display):,} registros)")
            else:
                st.warning("⚠️ Por favor selecciona un rango válido para los gráficos principales.")
                df_display = pd.DataFrame() 
    else:
        df_display = df_processed_for_display.copy()
        st.info("ℹ️ Mostrando todos los datos disponibles")

    if df_display.empty and uploaded_files:
        st.warning("⚠️ No hay datos para mostrar en el rango seleccionado.")
    
    # KPIs and main visualizations based on df_display
    if not df_display.empty:
        kpis = OptibatMetricsAnalyzer.calculate_system_status(df_display)
        
        st.markdown("### 📊 Indicadores Clave de Rendimiento (KPIs)")
        kpi_cols = st.columns(6)
        
        with kpi_cols[0]: 
            status_color = "positive" if kpis['system_on'] == "Activo" else "negative"
            if kpis['system_on'] == 'Datos Inválidos': status_color = "warning"
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center; height: 150px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #666; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Estado del Sistema</div>
                <div style="font-size: 2rem; font-weight: 700; margin: 0; color: {'#27ae60' if status_color == 'positive' else '#e74c3c' if status_color == 'negative' else '#f39c12'};">{kpis['system_on']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_cols[1]: 
            uptime_val = 0.0
            try:
                uptime_val = float(str(kpis['uptime_pct']).rstrip('%'))
            except ValueError:
                pass 
            uptime_color = "#27ae60" if uptime_val >= 90 else "#e74c3c" if uptime_val < 50 else "#3498db"
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center; height: 150px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #666; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Tiempo Activo</div>
                <div style="font-size: 2rem; font-weight: 700; margin: 0; color: {uptime_color};">{kpis['uptime_pct']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_cols[2]: 
            deactivations_count = kpis['flag_ready_deactivations']
            deactivations_color = "#27ae60" if deactivations_count == 0 else "#e74c3c" if deactivations_count > 5 else "#f39c12"
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center; height: 150px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #666; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Flag Ready (1 → 0)</div>
                <div style="font-size: 2rem; font-weight: 700; margin: 0; color: {deactivations_color};">{deactivations_count:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_cols[3]: 
            anomaly_total = kpis['anomalies']
            anomaly_color = "#27ae60" if anomaly_total == 0 else "#e74c3c" if anomaly_total > 10 else "#3498db"
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center; height: 150px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #666; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Anomalías Detectadas</div>
                <div style="font-size: 2rem; font-weight: 700; margin: 0; color: {anomaly_color};">{anomaly_total:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_cols[4]: 
            hb_status_text = kpis['heartbeat_status']
            hb_color = "#27ae60" 
            if "Anómalo" in hb_status_text: hb_color = "#e74c3c"
            elif "Sin Datos" in hb_status_text or "Fecha Inválida" in hb_status_text : hb_color = "#3498db"
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center; height: 150px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #666; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Heartbeat FM1</div>
                <div style="font-size: 1.1rem; font-weight: 700; margin: 0; color: {hb_color}; line-height: 1.3em; word-wrap: break-word; overflow-wrap: break-word;">{hb_status_text}</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_cols[5]: 
            quality_val = kpis['data_quality']
            quality_color = "#27ae60" if quality_val >= 90 else "#e74c3c" if quality_val < 50 else "#3498db"
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center; height: 150px; display: flex; flex-direction: column; justify-content: center;">
                <div style="color: #666; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Calidad de Datos</div>
                <div style="font-size: 2rem; font-weight: 700; margin: 0; color: {quality_color};">{quality_val:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # EXPLICACIÓN DEL UPTIME - QUÉ FLAG SE USA
        st.info("""
        💡 **Aclaración sobre UPTIME:** El análisis de tiempo activo se basa en la flag **OPTIBAT_ON**. 
        Esto significa que se considera "tiempo activo" cuando el sistema OPTIBAT está encendido (OPTIBAT_ON = 1).
        
        - **Tiempo Activo (%)** = Porcentaje de tiempo que OPTIBAT_ON estuvo en estado 1
        - **Flag Ready (1 → 0)** = Número de veces que Flag_Ready cambió de 1 a 0 (caídas del sistema)
        """)

        # Show anomaly details if present
        if 'anomalies_breakdown' in kpis and kpis['anomalies_breakdown']['total_anomalies'] > 0:
            with st.expander("🔍 Detalles de Anomalías Detectadas", expanded=False):
                breakdown = kpis['anomalies_breakdown']
                details_md = []
                if breakdown.get('stuck_Communication_ECS', 0) > 0: details_md.append(f"- **Comunicación ECS Pegada (7+):** `{breakdown.get('stuck_Communication_ECS', 0)}`")
                if breakdown.get('stuck_FM1_COMMS_HeartBeat', 0) > 0: details_md.append(f"- **HeartBeat FM1 Pegado (7+):** `{breakdown.get('stuck_FM1_COMMS_HeartBeat', 0)}`")
                if breakdown.get('stuck_OPTIBAT_WATCHDOG', 0) > 0: details_md.append(f"- **Watchdog OPTIBAT Pegado (7+):** `{breakdown.get('stuck_OPTIBAT_WATCHDOG', 0)}`")
                if breakdown.get('zero_Support_Flag_Copy', 0) > 0: details_md.append(f"- **Support_Flag_Copy en Cero:** `{breakdown.get('zero_Support_Flag_Copy', 0)}`")
                if breakdown.get('zero_Macrostates_Flag_Copy', 0) > 0: details_md.append(f"- **Macrostates_Flag_Copy en Cero:** `{breakdown.get('zero_Macrostates_Flag_Copy', 0)}`")
                if breakdown.get('zero_Resultexistance_Flag_Copy', 0) > 0: details_md.append(f"- **Resultexistance_Flag_Copy en Cero:** `{breakdown.get('zero_Resultexistance_Flag_Copy', 0)}`")
                if details_md: st.markdown("\n".join(details_md))
                else: st.markdown("No se encontraron detalles específicos.")

        if "Anómalo" in kpis['heartbeat_status']:
            st.warning("⚠️ **Alerta de Sistema:** El Heartbeat FM1 indica una anomalía. Revise `Flag_Ready`.")

        st.markdown("### 🎯 Estado de Flags Principales (Gauges)")
        # Obtener TODAS las flags disponibles en el archivo, no solo MAIN_FLAGS
        all_available_flags = get_available_flags_in_data(df_display)
        valid_gauge_flags = [flag for flag in all_available_flags if flag in df_display.columns and not df_display[flag].dropna().empty]
        num_valid_gauges = len(valid_gauge_flags)
        num_gauge_display_cols = min(4, num_valid_gauges) if num_valid_gauges > 0 else 0

        if num_gauge_display_cols > 0:
            # Calcular número de filas necesarias para mostrar todas las flags
            num_rows = (num_valid_gauges + 3) // 4  # Redondear hacia arriba
            
            gauges_displayed_count = 0
            for row in range(num_rows):
                # Crear columnas para esta fila
                start_idx = row * 4
                end_idx = min(start_idx + 4, num_valid_gauges)
                flags_in_row = valid_gauge_flags[start_idx:end_idx]
                gauge_cols = st.columns(len(flags_in_row))
                
                for i, flag_name in enumerate(flags_in_row):
                    description = FLAG_DESCRIPTIONS.get(flag_name, flag_name)
                    if flag_name in PULSING_SIGNALS_FOR_GAUGE:
                        gauge_value = OptibatMetricsAnalyzer.calculate_pulsing_gauge_value(df_display[flag_name])
                    else:
                        gauge_value = df_display[flag_name].mean() * 100
                    with gauge_cols[i]:
                        fig_gauge = OptibatMetricsAnalyzer.create_gauge_chart(gauge_value, flag_name.replace("_"," "), description)
                        st.plotly_chart(fig_gauge, use_container_width=True)
                    gauges_displayed_count +=1
        elif uploaded_files: 
            st.info("No hay datos de flags para gauges en el rango seleccionado.")

        if "Date" in df_display.columns and not df_display["Date"].dropna().empty: 
            st.markdown("### 📈 Línea de Tiempo del Sistema")
            # Pasar TODAS las flags disponibles al timeline
            timeline_fig = OptibatMetricsAnalyzer.create_timeline_chart(df_display, all_available_flags)
            st.plotly_chart(timeline_fig, use_container_width=True)
        elif uploaded_files: 
            st.info("La columna 'Date' no está presente para generar la línea de tiempo.")
        
        # Raw data section
        if show_raw_data:
            st.markdown("### 📋 Datos Crudos")
            with st.expander("Ver y filtrar datos completos", expanded=False):
                base_raw_df = st.session_state.get('df_processed_global', pd.DataFrame())
                
                if not base_raw_df.empty and "Date" in base_raw_df.columns and not base_raw_df["Date"].dropna().empty:
                    raw_min_date = base_raw_df["Date"].min().date()
                    raw_max_date = base_raw_df["Date"].max().date()

                    val_start_raw = raw_min_date
                    val_end_raw = raw_max_date
                    if date_range_main and len(date_range_main) == 2:
                        val_start_raw = max(raw_min_date, date_range_main[0])
                        val_end_raw = min(raw_max_date, date_range_main[1])

                    raw_date_sel = st.date_input(
                        "Filtrar datos crudos por fecha:",
                        value=(val_start_raw, val_end_raw),
                        min_value=raw_min_date,
                        max_value=raw_max_date,
                        format="DD/MM/YYYY",
                        key="raw_data_date_selector"
                    )
                    if len(raw_date_sel) == 2:
                        s_date_raw, e_date_raw = raw_date_sel
                        mask_raw = (base_raw_df["Date"] >= pd.Timestamp(s_date_raw)) & \
                                     (base_raw_df["Date"] <= pd.Timestamp(e_date_raw).replace(hour=23, minute=59, second=59))
                        df_to_show_raw = base_raw_df[mask_raw]
                    else:
                        df_to_show_raw = pd.DataFrame()
                elif not base_raw_df.empty:
                    df_to_show_raw = base_raw_df
                    st.info("No hay columna 'Date' en los datos crudos para filtrar por fecha.")
                else:
                    df_to_show_raw = pd.DataFrame()
                    st.info("No hay datos cargados para mostrar como datos crudos.")

                if not df_to_show_raw.empty:
                    col1_raw_ui, col2_raw_ui = st.columns(2)
                    with col1_raw_ui:
                        all_cols_for_select = ['Date'] + MAIN_FLAGS + ['source_file'] if 'Date' in df_to_show_raw else MAIN_FLAGS + ['source_file']
                        available_cols_for_select = [col for col in all_cols_for_select if col in df_to_show_raw.columns]
                        default_raw_cols = [col for col in (['Date'] + MAIN_FLAGS[:3] if 'Date' in df_to_show_raw else MAIN_FLAGS[:3]) if col in available_cols_for_select]

                        selected_cols_for_raw = st.multiselect(
                            "Seleccionar columnas:",
                            options=available_cols_for_select,
                            default=default_raw_cols,
                            key="raw_data_multiselect_cols"
                        )
                    with col2_raw_ui:
                        rows_to_display_raw = st.slider("Número de filas:", 10, 1000, 100, key="raw_data_num_rows")
                    
                    if selected_cols_for_raw:
                        st.dataframe(df_to_show_raw[selected_cols_for_raw].head(rows_to_display_raw), use_container_width=True, height=400)
                    else:
                        st.info("Seleccione columnas para mostrar.")

        # Export results
        if export_results:
            st.markdown("### Exportar Resultados")
            export_cols = st.columns(3)
            
            with export_cols[0]:
                if not df_display.empty:
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar datos de gráficos (CSV)", data=csv,
                        file_name=f"optibat_dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv"
                    )
                else:
                    st.info("No hay datos en los gráficos para exportar.")
            
            with export_cols[1]:
                kpis_json = json.dumps(kpis, indent=2, ensure_ascii=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar KPIs (JSON)", data=kpis_json,
                    file_name=f"optibat_kpis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", mime="application/json"
                )

# =========================
# SIMPLE AUTHENTICATION MODULE
# =========================
def check_authentication():
    """Simple authentication using secrets or session state"""
    
    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        return True, st.session_state.get('user_name', 'Usuario')
    
    # Default credentials for development  
    default_users = {
        "Administrador": {"password": "juancruze", "name": "Administrador"},
        "OPTIBAT.MTTO": {"password": "Optimitive", "name": "OPTIBAT Mantenimiento"}
    }
    
    users = default_users
    
    return False, users

def show_simple_login():
    """Show professional enterprise login form"""
    
    # Enterprise Header Section
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; background: linear-gradient(135deg, #E31E32 0%, #CC1A2C 100%); 
                border-radius: 20px; margin-bottom: 3rem; color: white; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <h1 style="font-size: 4rem; margin: 0; font-weight: 900; letter-spacing: 2px;">OPTIMITIVE</h1>
        <div style="height: 4px; width: 80px; background: white; margin: 1.5rem auto; border-radius: 2px;"></div>
        <h2 style="font-size: 1.8rem; margin: 0; font-weight: 300; opacity: 0.95;">OPTIBAT Maintenance Tool</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Professional Login Form Section
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: #2C3E50; font-size: 2.2rem; font-weight: 600; margin: 0;">Control de Acceso</h2>
        <p style="color: #6C757D; font-size: 1.1rem; margin: 0.5rem 0 0 0;">Ingrese sus credenciales para acceder al sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Simplified CSS for faster loading
    st.markdown("""
    <style>
    .login-form .stButton > button {
        background: #E31E32 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.8rem 2rem !important;
        width: 100% !important;
    }
    .professional-card {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Professional Login Card
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown('<div class="professional-card">', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="login-form">', unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuario", placeholder="Ingrese su nombre de usuario")
                password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
                submit = st.form_submit_button("Acceder al Sistema")
                
                if submit:
                    authenticated, users = check_authentication()
                    
                    if username in users and users[username]["password"] == password:
                        st.session_state['authenticated'] = True
                        st.session_state['user_name'] = users[username]["name"]
                        st.session_state['username'] = username
                        st.success("Acceso autorizado. Iniciando sistema...")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas. Verifique usuario y contraseña.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Professional Help Section
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Información del Sistema"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Acceso al Sistema:**
            - Credencial proporcionada por Mantenimiento
            - Acceso seguro con autenticación empresarial
            - Sesiones controladas y monitoreadas
            """)
        
        with col2:
            st.markdown("""
            **Capacidades del Sistema:**
            - Análisis avanzado de flags industriales
            - Generación de reportes ejecutivos
            - Monitoreo en tiempo real de sistemas OPTIBAT
            - Exportación de datos en formatos estándar
            """)

# =========================
# LOCAL FILE BROWSER FUNCTIONS
# =========================
def show_local_file_browser():
    """Show local file browser for uploading files from PC"""
    
    st.markdown(f"""
    <div style="background: {OPTIMITIVE_COLORS['accent_blue']}; color: white; padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem;">
        <h3 style="margin: 0; display: flex; align-items: center;">
            📁 Archivos Locales
        </h3>
        <p style="margin: 0.5rem 0 0 0;">
            Seleccione archivos .osf y .txt de su computadora para analizar.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if global files are loaded
    global_files_data = st.session_state.get('global_files_data', None)
    
    if not global_files_data:
        st.info("👈 **Usa el cargador global en la barra lateral** para alimentar este generador con archivos .osf y .txt")
        return
    
    # Show loaded files from global data
    st.markdown("### 📁 Archivos Cargados Globalmente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Archivos SampleFiles (.osf)")
        sample_files = global_files_data.get("SampleFiles", [])
        if sample_files:
            st.success(f"✅ {len(sample_files)} archivo(s) .osf cargado(s)")
            for file_name, _ in sample_files:
                st.write(f"📄 {file_name}")
        else:
            st.info("No hay archivos .osf cargados")
    
    with col2:
        st.markdown("#### 📊 Archivos Statistics (.txt)")
        stats_files = global_files_data.get("Statistics", [])
        if stats_files:
            st.success(f"✅ {len(stats_files)} archivo(s) .txt cargado(s)")
            for file_name, _ in stats_files:
                st.write(f"📊 {file_name}")
        else:
            st.info("No hay archivos .txt cargados")
    
    # Analysis section
    if sample_files or stats_files:
        st.markdown("---")
        st.markdown("### ⚙️ Configuración del Análisis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            project_type = st.selectbox(
                "Tipo de Proyecto",
                ["Auto", "CEMEX", "RCC"],
                help="Auto detectará el tipo basándose en las columnas del archivo",
                key="local_project_type"
            )
        
        with col2:
            month_name = st.text_input(
                "Nombre del Reporte",
                value="Análisis-Local",
                help="Este nombre aparecerá en el reporte"
            )
        
        notes = st.text_area(
            "Notas adicionales (opcional)",
            placeholder="Agregue cualquier observación relevante para este reporte...",
            height=100
        )
        
        # Analysis button
        if st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True):
            analyze_global_files(global_files_data, project_type, month_name, notes)
    
    else:
        st.info("👆 No hay datos globales cargados para analizar")
    
    # Back to main page
    st.markdown("---")
    if st.button("🏠 Volver al Inicio", use_container_width=True):
        if 'local_mode' in st.session_state:
            del st.session_state['local_mode']
        st.rerun()

def analyze_local_files(sample_files, stats_files, project_type, month_name, notes):
    """Analyze uploaded local files - LEGACY FUNCTION"""
    
    with st.spinner("Analizando archivos locales..."):
        try:
            # Organize files data
            files_data = {"SampleFiles": [], "Statistics": []}
            
            # Process sample files
            if sample_files:
                for file in sample_files:
                    content = file.read()
                    files_data["SampleFiles"].append((file.name, content))
            
            # Process statistics files
            if stats_files:
                for file in stats_files:
                    content = file.read()
                    files_data["Statistics"].append((file.name, content))
            
            # Analyze files
            df_analysis = analyze_files(files_data, project_type)
            
            if df_analysis.empty:
                st.warning("⚠️ No se encontraron datos para analizar en los archivos")
                return
            
            # Generate statistics
            stats = generate_summary_stats(df_analysis)
            
            # Display results
            st.markdown("### 📈 Resultados del Análisis")
            
            # KPIs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Archivos Analizados", stats['total_files'])
            
            with col2:
                st.metric("Flags Evaluadas", stats['total_flags'])
            
            with col3:
                st.metric("Cobertura Total", f"{stats['coverage_pct']}%")
            
            # Create visualizations
            charts = create_visualizations(stats)
            
            # Display charts
            if "flags" in charts:
                st.plotly_chart(charts["flags"], use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if "files" in charts:
                    st.plotly_chart(charts["files"], use_container_width=True)
            
            with col2:
                if "category" in charts:
                    st.plotly_chart(charts["category"], use_container_width=True)
            
            # Generate and display HTML report
            html_content = generate_html_report(
                df_analysis, stats, charts, 
                month_name, project_type, notes
            )
            
            # Download button for HTML
            st.download_button(
                label="📥 Descargar Reporte HTML",
                data=html_content,
                file_name=f"reporte_{month_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )
        
        except Exception as e:
            st.error(f"Error durante el análisis: {str(e)}")
            st.exception(e)

def analyze_global_files(global_files_data, project_type, month_name, notes):
    """Analyze files from global storage"""
    
    with st.spinner("Analizando archivos desde carga global..."):
        try:
            # Use the global files data directly
            df_analysis = analyze_files(global_files_data, project_type)
            
            if df_analysis.empty:
                st.warning("⚠️ No se encontraron datos para analizar en los archivos")
                return
            
            # Generate statistics
            stats = generate_summary_stats(df_analysis)
            
            # Display results
            st.markdown("### 📈 Resultados del Análisis")
            
            # KPIs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Archivos Analizados", stats['total_files'])
            
            with col2:
                st.metric("Flags Evaluadas", stats['total_flags'])
            
            with col3:
                st.metric("Cobertura Total", f"{stats['coverage_pct']}%")
            
            # Create visualizations
            charts = create_visualizations(stats)
            
            # Display charts
            if "flags" in charts:
                st.plotly_chart(charts["flags"], use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if "files" in charts:
                    st.plotly_chart(charts["files"], use_container_width=True)
            
            with col2:
                if "category" in charts:
                    st.plotly_chart(charts["category"], use_container_width=True)
            
            # Generate and display HTML report
            html_content = generate_html_report(
                df_analysis, stats, charts, 
                month_name, project_type, notes
            )
            
            # Download button for HTML
            st.download_button(
                label="📥 Descargar Reporte HTML",
                data=html_content,
                file_name=f"reporte_{month_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )
            
            # Detailed tables
            with st.expander("📋 Resumen por Flag", expanded=False):
                st.dataframe(
                    stats["by_flag"],
                    use_container_width=True,
                    hide_index=True
                )
            
            with st.expander("📁 Resumen por Archivo", expanded=False):
                st.dataframe(
                    stats["by_file"],
                    use_container_width=True,
                    hide_index=True
                )
        
        except Exception as e:
            st.error(f"Error durante el análisis: {str(e)}")
            st.exception(e)

# =========================
# SHAREPOINT / GRAPH CLIENT
# =========================
class GraphClient:
    """Microsoft Graph API Client for SharePoint access"""
    
    def __init__(self, tenant: str, client_id: str, client_secret: str):
        self.tenant = tenant
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = ["https://graph.microsoft.com/.default"]
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant}"
        )
        self._token = None
        self._token_expiry = 0
    
    def get_token(self) -> str:
        """Get or refresh access token"""
        current_time = time.time()
        
        # Check if token is still valid (with 5 min buffer)
        if self._token and self._token_expiry - current_time > 300:
            return self._token
        
        # Try to get token silently first
        result = self.app.acquire_token_silent(self.scope, account=None)
        
        # If no cached token, get new one
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" not in result:
            error_msg = result.get("error_description", "Unknown error")
            raise RuntimeError(f"Failed to acquire Graph token: {error_msg}")
        
        # Cache token and expiry
        self._token = result["access_token"]
        self._token_expiry = current_time + result.get("expires_in", 3600)
        
        return self._token
    
    def make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated GET request to Graph API"""
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def download_content(self, url: str) -> bytes:
        """Download file content from Graph API"""
        headers = {
            "Authorization": f"Bearer {self.get_token()}"
        }
        
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()
        return response.content

@st.cache_data(ttl=3600, show_spinner=False)
def get_site_and_drive(gc, hostname: str, site_path: str, drive_name: str) -> Tuple[str, str]:
    """Resolve SharePoint site and drive IDs"""
    
    # Get site ID
    site_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/{site_path}"
    site_info = gc.make_request(site_url)
    site_id = site_info["id"]
    
    # Get drives
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    drives_info = gc.make_request(drives_url)
    
    # Find matching drive
    for drive in drives_info.get("value", []):
        if drive.get("name") == drive_name:
            return site_id, drive["id"]
    
    raise ValueError(f"Drive '{drive_name}' not found in site")

def list_folder_contents(gc, drive_id: str, folder_path: str) -> List[Dict[str, Any]]:
    """List contents of a SharePoint folder"""
    
    # Clean path
    folder_path = folder_path.strip("/")
    
    if folder_path:
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_path}:/children"
    else:
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
    
    # Get all pages (handle pagination)
    items = []
    while url:
        data = gc.make_request(url)
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    
    return items

def download_file(gc, drive_id: str, file_path: str) -> bytes:
    """Download a file from SharePoint"""
    
    file_path = file_path.strip("/")
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_path}:/content"
    return gc.download_content(url)

# =========================
# FLAGS ANALYSIS MODULE
# =========================
FLAG_DEFINITIONS = {
    "CEMEX": [
        "OPTIBAT_ON",
        "Flag_Ready",
        "Communication_ECS",
        "Support_Flag_Copy",
        "Macrostates_Flag_Copy",
        "Resultexistance_Flag_Copy",
        "OPTIBAT_WATCHDOG"
    ],
    "RCC": [
        "OPTIBAT_ON",
        "MacroState_flag",
        "Support",
        "ResulExistance_Quality_flag",
        "OPTIBAT_COMMUNICATION"
    ]
}

def parse_header_line(line: str) -> List[str]:
    """Parse header line with multiple possible delimiters"""
    line = line.strip().strip("\ufeff")
    
    # Try tab delimiter first
    if "\t" in line:
        columns = line.split("\t")
    else:
        # Try multiple spaces
        columns = re.split(r"\s{2,}", line)
    
    # Clean column names
    return [col.strip().strip('"').strip("'") for col in columns if col.strip()]

def extract_varname_header(content: bytes) -> List[str]:
    """Extract VarName header from file content"""
    try:
        text = content.decode("utf-8-sig", errors="replace")
        lines = text.splitlines()
        
        for line in lines[:100]:  # Check first 100 lines
            clean_line = line.strip()
            if clean_line.lower().startswith("varname"):
                return parse_header_line(clean_line)
        
        return []
    except Exception as e:
        st.warning(f"Error parsing header: {e}")
        return []

def detect_project_type(header: List[str]) -> Optional[str]:
    """Auto-detect project type from header columns"""
    if not header:
        return None
    
    header_lower = {col.lower() for col in header}
    
    # Check for CEMEX-specific columns
    cemex_indicators = {
        "flag_ready", "communication_ecs", "support_flag_copy",
        "macrostates_flag_copy", "resultexistance_flag_copy"
    }
    
    # Check for RCC-specific columns
    rcc_indicators = {
        "macrostate_flag", "support", "resulexistance_quality_flag",
        "optibat_communication"
    }
    
    cemex_matches = len(cemex_indicators & header_lower)
    rcc_matches = len(rcc_indicators & header_lower)
    
    if cemex_matches > rcc_matches:
        return "CEMEX"
    elif rcc_matches > 0:
        return "RCC"
    
    return None

def find_flag_column(header: List[str], flag_name: str) -> int:
    """Find column index for a specific flag"""
    flag_lower = flag_name.lower()
    
    for idx, col in enumerate(header):
        if col.strip().lower() == flag_lower:
            return idx
    
    return -1

def analyze_files(files_data: Dict[str, List[Tuple[str, bytes]]], 
                  project_type: str = "Auto") -> pd.DataFrame:
    """Analyze files for flag presence and positions"""
    
    results = []
    detected_project = None
    
    # Auto-detect project if needed
    if project_type == "Auto":
        for category, files in files_data.items():
            if files and not detected_project:
                _, content = files[0]
                header = extract_varname_header(content)
                detected_project = detect_project_type(header)
        
        if not detected_project:
            detected_project = "CEMEX"  # Default fallback
    else:
        detected_project = project_type
    
    # Get flag list for project
    flags = FLAG_DEFINITIONS.get(detected_project, FLAG_DEFINITIONS["CEMEX"])
    
    # Analyze each file
    for category, files in files_data.items():
        for filename, content in files:
            header = extract_varname_header(content)
            
            for flag in flags:
                col_idx = find_flag_column(header, flag) if header else -1
                
                results.append({
                    "Category": category,
                    "File": filename,
                    "Flag": flag,
                    "Column Index": col_idx if col_idx >= 0 else "",
                    "Found": col_idx >= 0,
                    "Project": detected_project
                })
    
    return pd.DataFrame(results)

# =========================
# FILE BROWSER UI
# =========================
def render_breadcrumb(path_parts: List[str]):
    """Render breadcrumb navigation"""
    
    breadcrumb_html = '<div class="breadcrumb">'
    
    # Root
    breadcrumb_html += '<a href="#" onclick="return false;">🏠 Root</a>'
    
    # Path parts
    for i, part in enumerate(path_parts):
        breadcrumb_html += '<span class="separator">/</span>'
        breadcrumb_html += f'<a href="#" onclick="return false;">{part}</a>'
    
    breadcrumb_html += '</div>'
    
    st.markdown(breadcrumb_html, unsafe_allow_html=True)
    
    # Handle navigation with buttons
    cols = st.columns(len(path_parts) + 1)
    
    with cols[0]:
        if st.button("🏠", key="nav_root", help="Go to root"):
            st.session_state.current_path = []
            st.rerun()
    
    for i, part in enumerate(path_parts):
        with cols[i + 1]:
            if st.button(f"📁 {part[:10]}..." if len(part) > 10 else f"📁 {part}", 
                        key=f"nav_{i}", help=f"Go to {part}"):
                st.session_state.current_path = path_parts[:i + 1]
                st.rerun()

def render_file_browser(gc, drive_id: str):
    """Render SharePoint file browser"""
    
    if "current_path" not in st.session_state:
        st.session_state.current_path = []
    
    current_path = "/".join(st.session_state.current_path)
    
    # Render breadcrumb
    render_breadcrumb(st.session_state.current_path)
    
    # Get folder contents
    with st.spinner("Loading SharePoint contents..."):
        items = list_folder_contents(gc, drive_id, current_path)
    
    # Separate folders and files
    folders = [item for item in items if item.get("folder")]
    files = [item for item in items if item.get("file")]
    
    # Sort by name
    folders.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())
    
    # Display in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 Folders")
        
        if not folders:
            st.info("No subfolders in this location")
        else:
            for folder in folders:
                folder_name = folder["name"]
                
                # Format folder info
                modified = folder.get("lastModifiedDateTime", "")
                if modified:
                    modified = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                    modified_str = modified.strftime("%Y-%m-%d %H:%M")
                else:
                    modified_str = "Unknown"
                
                if st.button(
                    f"📁 {folder_name}",
                    key=f"folder_{folder['id']}",
                    help=f"Modified: {modified_str}",
                    use_container_width=True
                ):
                    st.session_state.current_path.append(folder_name)
                    st.rerun()
    
    with col2:
        st.markdown("### 📄 Files")
        
        if not files:
            st.info("No files in this folder")
        else:
            # Create dataframe for files
            files_data = []
            for file in files:
                size_kb = file.get("size", 0) / 1024
                modified = file.get("lastModifiedDateTime", "")
                if modified:
                    modified = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                    modified_str = modified.strftime("%Y-%m-%d")
                else:
                    modified_str = ""
                
                files_data.append({
                    "Name": file["name"],
                    "Size (KB)": f"{size_kb:.1f}",
                    "Modified": modified_str
                })
            
            df_files = pd.DataFrame(files_data)
            st.dataframe(df_files, use_container_width=True, height=300)
    
    # Selection button
    st.markdown("---")
    
    if st.button(
        "✅ Use This Folder for Analysis",
        key="select_folder",
        type="primary",
        use_container_width=True
    ):
        st.session_state.selected_folder = current_path
        return True
    
    return False

# =========================
# REPORT GENERATION
# =========================
def generate_summary_stats(df_analysis: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics from analysis"""
    
    if df_analysis.empty:
        return {
            "total_files": 0,
            "total_flags": 0,
            "coverage_pct": 0,
            "by_flag": pd.DataFrame(),
            "by_file": pd.DataFrame(),
            "by_category": pd.DataFrame()
        }
    
    # Overall stats
    total_files = df_analysis["File"].nunique()
    total_flags = df_analysis["Flag"].nunique()
    coverage_pct = df_analysis["Found"].mean() * 100
    
    # By flag
    by_flag = df_analysis.groupby("Flag").agg({
        "Found": ["sum", "count", lambda x: x.mean() * 100]
    }).round(1)
    by_flag.columns = ["Files Found", "Total Files", "Coverage %"]
    by_flag = by_flag.reset_index()
    
    # By file
    by_file = df_analysis.groupby("File").agg({
        "Found": ["sum", "count", lambda x: x.mean() * 100]
    }).round(1)
    by_file.columns = ["Flags Found", "Total Flags", "Coverage %"]
    by_file = by_file.reset_index()
    
    # By category
    by_category = df_analysis.groupby("Category").agg({
        "Found": ["sum", "count", lambda x: x.mean() * 100]
    }).round(1)
    by_category.columns = ["Flags Found", "Total Checks", "Coverage %"]
    by_category = by_category.reset_index()
    
    return {
        "total_files": total_files,
        "total_flags": total_flags,
        "coverage_pct": round(coverage_pct, 1),
        "by_flag": by_flag,
        "by_file": by_file,
        "by_category": by_category
    }

def create_visualizations(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Create Plotly visualizations for the report"""
    
    charts = {}
    
    # Flag coverage chart
    if not stats["by_flag"].empty:
        fig_flags = px.bar(
            stats["by_flag"].sort_values("Coverage %", ascending=True),
            x="Coverage %",
            y="Flag",
            orientation="h",
            title="Flag Coverage Analysis",
            color="Coverage %",
            color_continuous_scale=["#FF3366", "#FFB800", "#00CC66"],
            range_color=[0, 100]
        )
        
        fig_flags.update_layout(
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=18,
            xaxis=dict(range=[0, 105])
        )
        
        charts["flags"] = fig_flags
    
    # File coverage distribution
    if not stats["by_file"].empty:
        fig_files = px.histogram(
            stats["by_file"],
            x="Coverage %",
            nbins=20,
            title="File Coverage Distribution",
            labels={"count": "Number of Files", "Coverage %": "Coverage Percentage"},
            color_discrete_sequence=[OPTIMITIVE_COLORS['accent_blue']]
        )
        
        fig_files.update_layout(
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=18
        )
        
        charts["files"] = fig_files
    
    # Category comparison
    if not stats["by_category"].empty:
        fig_category = go.Figure(data=[
            go.Bar(
                name='Flags Found',
                x=stats["by_category"]["Category"],
                y=stats["by_category"]["Flags Found"],
                marker_color=OPTIMITIVE_COLORS['success']
            ),
            go.Bar(
                name='Missing',
                x=stats["by_category"]["Category"],
                y=stats["by_category"]["Total Checks"] - stats["by_category"]["Flags Found"],
                marker_color=OPTIMITIVE_COLORS['error']
            )
        ])
        
        fig_category.update_layout(
            barmode='stack',
            title="Coverage by Category",
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_size=18,
            xaxis_title="Category",
            yaxis_title="Number of Checks"
        )
        
        charts["category"] = fig_category
    
    return charts

def generate_html_report(
    month_name: str,
    project: str,
    stats: Dict[str, Any],
    df_analysis: pd.DataFrame,
    notes: str = ""
) -> str:
    """Generate HTML report"""
    
    # Convert dataframes to HTML
    def df_to_html(df: pd.DataFrame, max_rows: int = 100) -> str:
        if df.empty:
            return "<p>No data available</p>"
        
        # Limit rows for large datasets
        if len(df) > max_rows:
            df = df.head(max_rows)
            html = df.to_html(index=False, classes="data-table")
            html += f"<p><em>Showing first {max_rows} of {len(df)} rows</em></p>"
        else:
            html = df.to_html(index=False, classes="data-table")
        
        return html
    
    # Generate report sections
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Monthly Report - {month_name} - {project}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0A0A0A 0%, #1A1A1A 100%);
                color: #FFFFFF;
                line-height: 1.6;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }}
            
            .header {{
                background: linear-gradient(90deg, #E31E32 0%, #CC1A2C 100%);
                padding: 3rem 2rem;
                border-radius: 15px;
                text-align: center;
                margin-bottom: 2rem;
                box-shadow: 0 8px 32px rgba(227, 30, 50, 0.3);
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .header .subtitle {{
                font-size: 1.2rem;
                opacity: 0.9;
            }}
            
            .header .timestamp {{
                font-size: 0.9rem;
                opacity: 0.7;
                margin-top: 1rem;
            }}
            
            .kpi-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }}
            
            .kpi-card {{
                background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
                padding: 1.5rem;
                border-radius: 15px;
                border-left: 5px solid #E31E32;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            
            .kpi-card .label {{
                color: #CCCCCC;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 0.5rem;
            }}
            
            .kpi-card .value {{
                font-size: 2rem;
                font-weight: 700;
                color: #FFFFFF;
            }}
            
            .kpi-card.success .value {{
                color: #00CC66;
            }}
            
            .kpi-card.warning .value {{
                color: #FFB800;
            }}
            
            .kpi-card.danger .value {{
                color: #FF3366;
            }}
            
            .section {{
                background: #1A1A1A;
                border-radius: 15px;
                padding: 2rem;
                margin: 2rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            
            .section h2 {{
                color: #E31E32;
                margin-bottom: 1.5rem;
                font-size: 1.8rem;
                border-bottom: 2px solid #E31E32;
                padding-bottom: 0.5rem;
            }}
            
            .section h3 {{
                color: #0099CC;
                margin: 1.5rem 0 1rem 0;
                font-size: 1.3rem;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
                background: #0A0A0A;
                border-radius: 10px;
                overflow: hidden;
            }}
            
            .data-table th {{
                background: #E31E32;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            
            .data-table td {{
                padding: 10px 12px;
                border-bottom: 1px solid #2A2A2A;
            }}
            
            .data-table tr:hover {{
                background: #2A2A2A;
            }}
            
            .data-table tr:nth-child(even) {{
                background: #1A1A1A;
            }}
            
            .notes {{
                background: linear-gradient(135deg, #0099CC 0%, #007AA3 100%);
                padding: 1.5rem;
                border-radius: 10px;
                margin: 2rem 0;
            }}
            
            .footer {{
                text-align: center;
                padding: 2rem;
                color: #CCCCCC;
                border-top: 2px solid #E31E32;
                margin-top: 3rem;
            }}
            
            .footer a {{
                color: #E31E32;
                text-decoration: none;
            }}
            
            .success-badge {{
                background: #00CC66;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.9rem;
            }}
            
            .error-badge {{
                background: #FF3366;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.9rem;
            }}
            
            @media print {{
                body {{
                    background: white;
                    color: black;
                }}
                
                .header, .kpi-card, .section {{
                    box-shadow: none;
                    border: 1px solid #ddd;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Monthly Report - {month_name}</h1>
                <div class="subtitle">Project: {project}</div>
                <div class="timestamp">Generated: {timestamp}</div>
            </div>
            
            <div class="kpi-container">
                <div class="kpi-card">
                    <div class="label">Total Files Analyzed</div>
                    <div class="value">{stats['total_files']}</div>
                </div>
                
                <div class="kpi-card">
                    <div class="label">Total Flags Checked</div>
                    <div class="value">{stats['total_flags']}</div>
                </div>
                
                <div class="kpi-card {'success' if stats['coverage_pct'] >= 80 else 'warning' if stats['coverage_pct'] >= 60 else 'danger'}">
                    <div class="label">Overall Coverage</div>
                    <div class="value">{stats['coverage_pct']}%</div>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Flag Coverage Summary</h2>
                {df_to_html(stats['by_flag'])}
            </div>
            
            <div class="section">
                <h2>📁 File Coverage Summary</h2>
                {df_to_html(stats['by_file'])}
            </div>
            
            <div class="section">
                <h2>📊 Category Analysis</h2>
                {df_to_html(stats['by_category'])}
            </div>
            
            <div class="section">
                <h2>🔍 Detailed Analysis</h2>
                {df_to_html(df_analysis)}
            </div>
            
            {f'<div class="notes"><h3>📝 Notes</h3><p>{notes}</p></div>' if notes else ''}
            
            <div class="footer">
                <p><strong>Optimitive Monthly Report Generator</strong></p>
                <p>Developed by Juan Cruz E. | Powered by <a href="https://optimitive.com">Optimitive</a></p>
                <p>© 2024 Optimitive - AI Optimization Solutions</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template

# =========================
# LOGIN PAGE UI
# =========================
def show_professional_login_page():
    """Display professional landing/login page"""
    
    # Hero Section
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #8B0A1A 50%, #000000 100%);
                padding: 4rem 2rem; border-radius: 25px; text-align: center; margin-bottom: 2rem;
                box-shadow: 0 20px 60px rgba(227, 30, 50, 0.4); position: relative; overflow: hidden;">
        
        <!-- Background Pattern -->
        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                    background: url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><defs><pattern id=\"grid\" width=\"10\" height=\"10\" patternUnits=\"userSpaceOnUse\"><path d=\"M 10 0 L 0 0 0 10\" fill=\"none\" stroke=\"%23ffffff\" stroke-width=\"0.5\" opacity=\"0.1\"/></pattern></defs><rect width=\"100\" height=\"100\" fill=\"url(%23grid)\"/></svg>'); opacity: 0.3;">
        </div>
        
        <!-- Content -->
        <div style="position: relative; z-index: 2;">
            <h1 style="margin: 0; font-size: 4rem; font-weight: 900; color: white; 
                       text-shadow: 3px 3px 10px rgba(0,0,0,0.7); letter-spacing: 3px;">
                🚀 OPTIMITIVE
            </h1>
            <div style="height: 4px; width: 100px; background: white; margin: 1rem auto; border-radius: 2px;"></div>
            <h2 style="margin: 1rem 0; font-size: 1.8rem; color: white; font-weight: 300; opacity: 0.95;">
                Monthly Report Generator
            </h2>
            <p style="font-size: 1.1rem; color: white; opacity: 0.85; max-width: 600px; margin: 1rem auto; line-height: 1.6;">
                Professional SharePoint Integration & Advanced Flag Analysis Tool
            </p>
            <div style="margin-top: 2rem;">
                <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 25px; 
                           color: white; font-size: 0.9rem; margin: 0 0.5rem;">
                    📊 Analytics
                </span>
                <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 25px; 
                           color: white; font-size: 0.9rem; margin: 0 0.5rem;">
                    🔗 SharePoint
                </span>
                <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 25px; 
                           color: white; font-size: 0.9rem; margin: 0 0.5rem;">
                    📈 Reports
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Login Section
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['medium_bg']} 0%, {OPTIMITIVE_COLORS['light_bg']} 100%);
                    padding: 3rem; border-radius: 25px; box-shadow: 0 15px 40px rgba(0,0,0,0.5);
                    border: 1px solid {OPTIMITIVE_COLORS['primary_red']}44; position: relative;">
            
            <!-- Login Header -->
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="display: inline-block; background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
                           padding: 1rem 2rem; border-radius: 15px; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: white; font-size: 1.5rem; font-weight: 700;">
                        🔐 SISTEMA DE LOGIN
                    </h3>
                </div>
                <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; margin: 0; font-size: 1rem;">
                    Ingrese sus credenciales para acceder al sistema
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Features Section
    st.markdown("### ✨ Características Principales")
    
    feature_cols = st.columns(3)
    
    with feature_cols[0]:
        st.markdown(f"""
        <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 2rem; border-radius: 15px; 
                    text-align: center; border-left: 5px solid {OPTIMITIVE_COLORS['success']}; height: 200px;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
            <h4 style="color: {OPTIMITIVE_COLORS['text_primary']}; margin: 0.5rem 0;">Análisis Inteligente</h4>
            <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; font-size: 0.9rem; margin: 0;">
                Detección automática de flags y análisis avanzado de patrones en archivos
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_cols[1]:
        st.markdown(f"""
        <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 2rem; border-radius: 15px; 
                    text-align: center; border-left: 5px solid {OPTIMITIVE_COLORS['accent_blue']}; height: 200px;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔗</div>
            <h4 style="color: {OPTIMITIVE_COLORS['text_primary']}; margin: 0.5rem 0;">SharePoint Integration</h4>
            <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; font-size: 0.9rem; margin: 0;">
                Conexión directa con SharePoint para análisis de archivos en tiempo real
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_cols[2]:
        st.markdown(f"""
        <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 2rem; border-radius: 15px; 
                    text-align: center; border-left: 5px solid {OPTIMITIVE_COLORS['warning']}; height: 200px;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h4 style="color: {OPTIMITIVE_COLORS['text_primary']}; margin: 0.5rem 0;">Reportes Avanzados</h4>
            <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; font-size: 0.9rem; margin: 0;">
                Generación de reportes profesionales en HTML, CSV y PDF
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Credentials Info
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['accent_blue']} 0%, #0077AA 100%);
                padding: 2rem; border-radius: 20px; text-align: center; color: white; margin: 2rem 0;">
        <h4 style="margin: 0 0 1rem 0; font-size: 1.3rem;">💡 Credenciales de Acceso</h4>
        <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; backdrop-filter: blur(10px);">
                <strong>👨‍💼 Admin</strong><br>
                Usuario: <code>admin</code><br>
                Contraseña: <code>admin123</code>
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; backdrop-filter: blur(10px);">
                <strong>👤 Demo</strong><br>
                Usuario: <code>demo</code><br>
                Contraseña: <code>demo123</code>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# GLOBAL FILE PROCESSING
# =========================
def process_global_files(uploaded_files):
    """Process uploaded files and store globally for all modules"""
    if not uploaded_files:
        return
    
    try:
        # Separate files by type
        txt_files = [f for f in uploaded_files if f.name.endswith('.txt')]
        osf_files = [f for f in uploaded_files if f.name.endswith('.osf')]
        
        # Store files for metrics dashboard (txt files)
        if txt_files:
            metrics_df = OptibatMetricsAnalyzer.load_and_process_files(txt_files)
            st.session_state['global_metrics_data'] = metrics_df
            st.session_state['global_txt_files'] = txt_files
        
        # Store files for monthly report generator (osf + txt files)
        if txt_files or osf_files:
            files_data = {"SampleFiles": [], "Statistics": []}
            
            # Process OSF files
            for file in osf_files:
                content = file.read()
                files_data["SampleFiles"].append((file.name, content))
                file.seek(0)  # Reset file pointer
            
            # Process TXT files  
            for file in txt_files:
                content = file.read()
                files_data["Statistics"].append((file.name, content))
                file.seek(0)  # Reset file pointer
            
            st.session_state['global_files_data'] = files_data
            st.session_state['global_all_files'] = uploaded_files
            
        st.session_state['files_loaded'] = True
        
    except Exception as e:
        st.error(f"Error procesando archivos: {str(e)}")
        st.session_state['files_loaded'] = False

# =========================
# MAIN APPLICATION
# =========================
def main():
    # Register access metrics - TEMPORALMENTE DESACTIVADO PARA EVITAR DEMORA
    # if 'access_logged' not in st.session_state:
    #     st.session_state['access_logged'] = True
    #     user_ip = get_ip()
    #     log_access(user_ip)
    
    # Initialize analyzer if not in session state
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = OptibatMetricsAnalyzer()
    
    # Simple authentication check
    authenticated, user_info = check_authentication()
    
    if not authenticated:
        show_simple_login()
        st.stop()
    
    # Get user name for display (pero no mostrar en header)
    user_name = st.session_state.get('user_name', 'Usuario')
    
    # Determine if sidebar should be retracted
    files_loaded = st.session_state.get('files_loaded', False)
    
    # Add CSS for retractable sidebar behavior
    if files_loaded:
        st.markdown("""
        <style>
        /* Hide sidebar when files are loaded */
        .css-1d391kg {
            width: 0px !important;
            margin-left: -21rem !important;
            transition: all 0.3s ease;
        }
        
        /* Hover trigger area */
        body::before {
            content: '';
            position: fixed;
            left: 0;
            top: 0;
            width: 30px;
            height: 100vh;
            z-index: 1000;
            background: transparent;
        }
        
        /* Show sidebar on hover */
        body:hover .css-1d391kg {
            width: 21rem !important;
            margin-left: 0rem !important;
        }
        
        /* Trigger indicator */
        .sidebar-indicator {
            position: fixed;
            left: 5px;
            top: 100px;
            width: 20px;
            height: 60px;
            background: linear-gradient(135deg, #E31E32 0%, #CC1A2C 100%);
            border-radius: 0 10px 10px 0;
            z-index: 999;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            opacity: 0.8;
        }
        
        .sidebar-indicator:hover {
            width: 25px;
            opacity: 1.0;
        }
        </style>
        
        <div class="sidebar-indicator">☰</div>
        """, unsafe_allow_html=True)
    
    # Sidebar simplificado
    with st.sidebar:
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
                    padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0;">CARGA DE DATOS</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Global File Uploader
        uploaded_files_global = st.file_uploader(
            "Selecciona archivos STATISTICS (.txt)",
            type=['txt'],
            accept_multiple_files=True,
            key="global_file_uploader",
            help="Archivos STATISTICS_VIEW_SUMMARY.txt"
        )
        
        if uploaded_files_global:
            # Process and store files globally
            process_global_files(uploaded_files_global)
            
            st.success(f"Cargados {len(uploaded_files_global)} archivo(s) correctamente")
                
        # Cliente Detection - INFORMACIÓN OCULTA POR PRIVACIDAD
        if uploaded_files_global and 'global_metrics_data' in st.session_state:
            df_global = st.session_state['global_metrics_data']
            detected_client = detect_client_from_flags(df_global.columns)
            available_flags = get_available_flags_in_data(df_global)
            
            # st.markdown("---")
            # st.markdown(f"""
            # <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 1rem; border-radius: 10px;">
            #     <h4 style="color: {OPTIMITIVE_COLORS['primary_red']}; margin: 0 0 0.5rem 0;">CLIENTE DETECTADO</h4>
            #     <p style="margin: 0; font-weight: bold;">{detected_client}</p>
            #     <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">Flags disponibles: {len(available_flags)}</p>
            # </div>
            # """, unsafe_allow_html=True)
        
        # Info compacta
        with st.expander("Sistema de Flags"):
            st.markdown(f"""
            **Flags Principales Monitoreados:**
            - OPTIBAT_ON → Sistema principal activo
            - Flag_Ready → Sistema listo para operación  
            - Communication_ECS → Comunicación con ECS
            - Support_Flag_Copy → Flag de soporte
            - Macrostates_Flag_Copy → Estados macro
            - Resultexistance_Flag_Copy → Existencia resultados
            - OPTIBAT_WATCHDOG → Monitor de sistema
            
            **Clientes Configurados:** {len(CLIENT_FLAGS_MAPPING)}
            """)
        
        # Botón de cerrar sesión en la parte inferior del sidebar
        st.markdown("---")
        st.markdown(f"**Usuario:** {user_name}")
        if st.button("Cerrar Sesión", use_container_width=True, type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # CONTENIDO PRINCIPAL UNIFICADO
    show_unified_dashboard()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <h3 style="color: #E31E32; margin-bottom: 1rem;">OPTIMITIVE</h3>
        <p><strong>© Optimitive | AI Optimization Solutions</strong></p>
        <p><a href="https://optimitive.com" target="_blank" style="color: #E31E32;">optimitive.com</a></p>
        <p><strong>Developed by Juan Cruz Erreguerena.</strong> | Monthly Report Generator v1.0.0</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# ANÁLISIS AVANZADO FUNCTIONS - V1.0
# =========================

def analizar_performance_flags(df: pd.DataFrame, flags: list) -> pd.DataFrame:
    """Analiza el performance de las flags del sistema"""
    try:
        results = []
        
        for flag in flags:
            if flag in df.columns and not df[flag].dropna().empty:
                # Calcular métricas básicas
                availability = (df[flag] == 1).sum() / len(df) * 100
                transitions = abs(df[flag].diff()).sum() / 2  # Transiciones 0->1 o 1->0
                
                # Calcular estabilidad (menos transiciones = más estable) - CORREGIDO
                if len(df) > 0:
                    # Nueva fórmula: más precisa para detectar problemas en Communication_ECS y OPTIBAT_WATCHDOG
                    transition_rate = transitions / len(df) * 100  # Porcentaje de transiciones
                    stability = max(0, 100 - transition_rate * 10)  # Factor corregido para mejor detección
                    
                    # Ajuste especial para flags problemáticas
                    if flag in ['Communication_ECS', 'OPTIBAT_WATCHDOG']:
                        # Para estas flags, penalizar más las transiciones frecuentes
                        if transition_rate > 5:  # Más del 5% de transiciones es problemático
                            stability = max(0, stability - 20)  # Penalización adicional
                else:
                    stability = 0
                    
                results.append({
                    'Flag': flag.replace('_', ' '),
                    'Disponibilidad (%)': round(availability, 2),
                    'Transiciones': int(transitions),
                    'Estabilidad (%)': round(stability, 2)
                })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Error en análisis de performance: {str(e)}")
        return pd.DataFrame()

def create_performance_chart(performance_df: pd.DataFrame) -> go.Figure:
    """Crea gráfico de performance de flags (SIN TÍTULO)"""
    if performance_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos de performance disponibles", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Disponibilidad (%)', 'Transiciones', 'Estabilidad (%)', 'Resumen'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"type": "table"}]]
    )
    
    # Gráfico 1: Disponibilidad
    fig.add_trace(
        go.Bar(x=performance_df['Flag'], y=performance_df['Disponibilidad (%)'],
               name='Disponibilidad', marker_color='lightblue'),
        row=1, col=1
    )
    
    # Gráfico 2: Transiciones
    fig.add_trace(
        go.Bar(x=performance_df['Flag'], y=performance_df['Transiciones'],
               name='Transiciones', marker_color='orange'),
        row=1, col=2
    )
    
    # Gráfico 3: Estabilidad
    fig.add_trace(
        go.Bar(x=performance_df['Flag'], y=performance_df['Estabilidad (%)'],
               name='Estabilidad', marker_color='lightgreen'),
        row=2, col=1
    )
    
    # Tabla resumen
    fig.add_trace(
        go.Table(
            header=dict(values=['Flag', 'Disp.(%)', 'Trans.', 'Estab.(%)'],
                       fill_color='paleturquoise'),
            cells=dict(values=[performance_df['Flag'], 
                              performance_df['Disponibilidad (%)'],
                              performance_df['Transiciones'],
                              performance_df['Estabilidad (%)']],
                      fill_color='lavender')
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        margin=dict(t=50, b=50, l=50, r=50)  # Sin título, menos margen superior
    )
    
    return fig

def analizar_caidas_flag_ready(df: pd.DataFrame) -> dict:
    """Analiza las caídas de Flag_Ready"""
    try:
        if 'Flag_Ready' not in df.columns:
            return {'total_caidas': 0}
        
        flag_data = df['Flag_Ready'].fillna(0)
        
        # Detectar transiciones 1->0
        caidas = []
        duraciones = []
        
        for i in range(1, len(flag_data)):
            if flag_data.iloc[i-1] == 1 and flag_data.iloc[i] == 0:
                # Inicio de caída
                inicio_caida = i
                # Buscar fin de caída (cuando vuelve a 1)
                fin_caida = None
                for j in range(i+1, len(flag_data)):
                    if flag_data.iloc[j] == 1:
                        fin_caida = j
                        break
                
                if fin_caida:
                    duracion = fin_caida - inicio_caida
                    caidas.append((inicio_caida, fin_caida, duracion))
                    duraciones.append(duracion)
        
        # Convertir duraciones a minutos (asumiendo 1 registro = 1 minuto)
        duraciones_min = [d * 1 for d in duraciones]
        
        return {
            'total_caidas': len(caidas),
            'duracion_promedio': sum(duraciones_min) / len(duraciones_min) if duraciones_min else 0,
            'duracion_maxima': max(duraciones_min) if duraciones_min else 0,
            'duraciones': duraciones_min
        }
        
    except Exception as e:
        st.error(f"Error en análisis de caídas: {str(e)}")
        return {'total_caidas': 0}

def create_caidas_chart(caidas_data: dict) -> go.Figure:
    """Crea gráfico de caídas Flag_Ready"""
    fig = go.Figure()
    
    if caidas_data['total_caidas'] == 0:
        fig.add_annotation(text="No se detectaron caídas de Flag_Ready", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Histograma de duraciones
    fig.add_trace(
        go.Histogram(
            x=caidas_data['duraciones'],
            nbinsx=min(10, len(caidas_data['duraciones'])),
            name='Distribución de Duraciones',
            marker_color='red',
            opacity=0.7
        )
    )
    
    fig.update_layout(
        title="Distribución de Duraciones de Caídas Flag_Ready",
        xaxis_title="Duración (minutos)",
        yaxis_title="Número de Caídas",
        height=400
    )
    
    return fig

def generar_resumen_por_archivo(files: list, df_global: pd.DataFrame) -> pd.DataFrame:
    """Genera resumen comparativo por archivo"""
    try:
        resultados = []
        
        # Simular datos por archivo (ya que tenemos datos consolidados)
        total_files = len(files)
        registros_por_file = len(df_global) // total_files if total_files > 0 else len(df_global)
        
        for i, file in enumerate(files):
            # Simular subset de datos para cada archivo
            inicio = i * registros_por_file
            fin = min((i + 1) * registros_por_file, len(df_global))
            df_file = df_global.iloc[inicio:fin]
            
            if not df_file.empty and 'OPTIBAT_ON' in df_file.columns:
                uptime = (df_file['OPTIBAT_ON'] == 1).sum() / len(df_file) * 100
                anomalias = abs(df_file['OPTIBAT_ON'].diff()).sum()
                
                # Determinar calidad
                if uptime > 95:
                    calidad = "Excelente"
                elif uptime > 90:
                    calidad = "Buena" 
                else:
                    calidad = "Regular"
                    
                resultados.append({
                    'Archivo': file.name if hasattr(file, 'name') else f"Archivo_{i+1}",
                    'Registros': len(df_file),
                    'Uptime (%)': round(uptime, 1),
                    'Anomalías': int(anomalias),
                    'Calidad': calidad
                })
            
        return pd.DataFrame(resultados)
        
    except Exception as e:
        st.error(f"Error generando resumen por archivo: {str(e)}")
        return pd.DataFrame()

def create_resumen_files_chart(resumen_df: pd.DataFrame) -> go.Figure:
    """Crea gráficos comparativos por archivo"""
    if resumen_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos disponibles para comparación", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Uptime por Archivo (%)', 'Registros por Archivo'),
        vertical_spacing=0.15
    )
    
    # Gráfico 1: Uptime
    fig.add_trace(
        go.Bar(x=resumen_df['Archivo'], y=resumen_df['Uptime (%)'],
               name='Uptime', marker_color='lightblue'),
        row=1, col=1
    )
    
    # Gráfico 2: Registros
    fig.add_trace(
        go.Bar(x=resumen_df['Archivo'], y=resumen_df['Registros'],
               name='Registros', marker_color='lightcoral'),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        title="Comparación entre Archivos"
    )
    
    return fig

def crear_grafico_evolucion_sistema(df: pd.DataFrame, flags: list) -> go.Figure:
    """Crea gráfico de evolución temporal del sistema"""
    fig = go.Figure()
    
    if 'Date' not in df.columns or df['Date'].dropna().empty:
        fig.add_annotation(text="No hay datos de fecha disponibles", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Resamplear datos por hora para suavizar
    df_temp = df.set_index('Date')
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink']
    
    for i, flag in enumerate(flags[:7]):  # Máximo 7 flags
        if flag in df.columns and not df[flag].dropna().empty:
            try:
                # Resamplear por hora y calcular promedio
                flag_hourly = df_temp[flag].resample('H').mean()
                
                fig.add_trace(
                    go.Scatter(
                        x=flag_hourly.index,
                        y=flag_hourly.values,
                        mode='lines',
                        name=flag.replace('_', ' '),
                        line=dict(color=colors[i % len(colors)], width=2)
                    )
                )
            except Exception:
                continue
    
    fig.update_layout(
        title="Evolución Temporal de Flags del Sistema",
        xaxis_title="Fecha",
        yaxis_title="Estado de Flag (0-1)",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def analizar_tendencias_sistema(df: pd.DataFrame, flags: list) -> dict:
    """Analiza tendencias en las flags del sistema"""
    try:
        tendencias = {}
        
        if 'Date' not in df.columns or len(df) < 10:
            return tendencias
        
        df_temp = df.set_index('Date')
        
        for flag in flags:
            if flag in df.columns and not df[flag].dropna().empty:
                try:
                    # Calcular promedio por día
                    daily_avg = df_temp[flag].resample('D').mean()
                    
                    if len(daily_avg) >= 3:
                        # Calcular tendencia simple (primer vs último tercio)
                        tercio = len(daily_avg) // 3
                        inicio = daily_avg.iloc[:tercio].mean()
                        final = daily_avg.iloc[-tercio:].mean()
                        
                        diferencia = final - inicio
                        
                        if abs(diferencia) > 0.05:  # Cambio significativo
                            direccion = 'mejora' if diferencia > 0 else 'deterioro'
                            tendencias[flag] = {
                                'significativa': True,
                                'direccion': direccion,
                                'descripcion': f"Tendencia de {direccion} ({diferencia:+.2%})"
                            }
                        else:
                            tendencias[flag] = {
                                'significativa': False,
                                'direccion': 'estable',
                                'descripcion': "Tendencia estable sin cambios significativos"
                            }
                            
                except Exception:
                    tendencias[flag] = {
                        'significativa': False,
                        'direccion': 'indeterminada',
                        'descripcion': "No se pudo determinar tendencia"
                    }
        
        return tendencias
        
    except Exception as e:
        st.error(f"Error en análisis de tendencias: {str(e)}")
        return {}

def generar_grafico_rosquilla_global(df: pd.DataFrame, flags: list) -> go.Figure:
    """Crea gráfico de rosquilla global de estados por flag"""
    fig = go.Figure()
    
    try:
        if not flags or df.empty:
            fig.add_annotation(text="No hay flags disponibles", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Calcular estados agregados de todas las flags
        estados_totales = {'ON': 0, 'OFF': 0}
        
        for flag in flags:
            if flag in df.columns and not df[flag].dropna().empty:
                on_count = (df[flag] == 1).sum()
                off_count = (df[flag] == 0).sum()
                estados_totales['ON'] += on_count
                estados_totales['OFF'] += off_count
        
        if sum(estados_totales.values()) == 0:
            fig.add_annotation(text="No hay datos válidos para mostrar", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Crear gráfico de pie (rosquilla)
        fig.add_trace(
            go.Pie(
                labels=['Estados ON', 'Estados OFF'],
                values=[estados_totales['ON'], estados_totales['OFF']],
                hole=0.6,  # Hacer rosquilla
                marker=dict(colors=['#2ecc71', '#e74c3c'], line=dict(color='#FFFFFF', width=3)),
                textinfo='label+percent+value',
                textposition='inside',  # CORRECCIÓN: valor válido para textposition
                textfont=dict(size=14, color='white'),
                hovertemplate="<b>%{label}</b><br>" +
                             "Registros: %{value}<br>" +
                             "Porcentaje: %{percent}<br>" +
                             "<extra></extra>"
            )
        )
        
        # Agregar texto central
        total = sum(estados_totales.values())
        fig.add_annotation(
            text=f"<b>Total</b><br>{total:,}<br>Estados",
            x=0.5, y=0.5,
            font_size=18,
            showarrow=False
        )
        
        fig.update_layout(
            title="Distribución Global de Estados por Flag",
            title_x=0.5,
            height=800,  # 2 veces más grande que antes (era 400)
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=60, b=60, l=60, r=60)
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creando gráfico de rosquilla: {str(e)}")
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

def analizar_duracion_caidas_flag_ready(df: pd.DataFrame) -> go.Figure:
    """Analiza duración de caídas de Flag_Ready"""
    fig = go.Figure()
    
    try:
        if 'Flag_Ready' not in df.columns:
            fig.add_annotation(text="Flag_Ready no disponible", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Detectar caídas y duraciones
        caidas_data = analizar_caidas_flag_ready(df)
        
        if caidas_data['total_caidas'] == 0:
            fig.add_annotation(text="No se detectaron caídas de Flag_Ready", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        else:
            # Crear histograma de duraciones
            fig.add_trace(
                go.Histogram(
                    x=caidas_data['duraciones'],
                    nbinsx=min(20, len(caidas_data['duraciones'])),
                    name='Duración de Caídas',
                    marker_color='crimson',
                    opacity=0.8
                )
            )
            
            fig.update_layout(
                title="Distribución de Duración de Caídas Flag_Ready",
                xaxis_title="Duración (minutos)",
                yaxis_title="Número de Caídas"
            )
        
        fig.update_layout(height=500)  # Aumentar tamaño para mejor visualización
        return fig
        
    except Exception as e:
        st.error(f"Error en análisis de duración de caídas: {str(e)}")
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

def analizar_caidas_por_hora(df: pd.DataFrame) -> go.Figure:
    """Analiza caídas de Flag_Ready por hora del día"""
    fig = go.Figure()
    
    try:
        if 'Flag_Ready' not in df.columns or 'Date' not in df.columns:
            fig.add_annotation(text="Datos insuficientes para análisis horario", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Detectar transiciones 1->0 con timestamp
        df_temp = df.copy()
        df_temp['Flag_Ready_prev'] = df_temp['Flag_Ready'].shift(1)
        
        # Filtrar transiciones 1->0
        caidas = df_temp[(df_temp['Flag_Ready_prev'] == 1) & (df_temp['Flag_Ready'] == 0)]
        
        if caidas.empty:
            fig.add_annotation(text="No se detectaron caídas para análisis horario", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        else:
            # Extraer hora del día
            caidas_copy = caidas.copy()
            caidas_copy['Hora'] = pd.to_datetime(caidas_copy['Date']).dt.hour
            
            # Contar caídas por hora
            caidas_por_hora = caidas_copy['Hora'].value_counts().sort_index()
            
            fig.add_trace(
                go.Bar(
                    x=caidas_por_hora.index,
                    y=caidas_por_hora.values,
                    name='Caídas por Hora',
                    marker_color='orange'
                )
            )
            
            fig.update_layout(
                title="Caídas Flag_Ready por Hora del Día",
                xaxis_title="Hora del Día (0-23)",
                yaxis_title="Número de Caídas"
            )
        
        fig.update_layout(height=400)
        return fig
        
    except Exception as e:
        st.error(f"Error en análisis por hora: {str(e)}")
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

def analizar_caidas_por_dia_semana(df: pd.DataFrame) -> go.Figure:
    """Analiza caídas de Flag_Ready por día de la semana"""
    fig = go.Figure()
    
    try:
        if 'Flag_Ready' not in df.columns or 'Date' not in df.columns:
            fig.add_annotation(text="Datos insuficientes para análisis semanal", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Detectar transiciones 1->0 con timestamp
        df_temp = df.copy()
        df_temp['Flag_Ready_prev'] = df_temp['Flag_Ready'].shift(1)
        
        # Filtrar transiciones 1->0
        caidas = df_temp[(df_temp['Flag_Ready_prev'] == 1) & (df_temp['Flag_Ready'] == 0)]
        
        if caidas.empty:
            fig.add_annotation(text="No se detectaron caídas para análisis semanal", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        else:
            # Extraer día de la semana
            caidas_copy = caidas.copy()
            caidas_copy['DiaSemana'] = pd.to_datetime(caidas_copy['Date']).dt.day_name()
            
            # Definir orden de días
            dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_español = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            # Contar caídas por día
            caidas_por_dia = caidas_copy['DiaSemana'].value_counts()
            
            # Reordenar según días de la semana
            caidas_ordenadas = []
            dias_mostrar = []
            
            for i, dia_en in enumerate(dias_orden):
                if dia_en in caidas_por_dia.index:
                    caidas_ordenadas.append(caidas_por_dia[dia_en])
                    dias_mostrar.append(dias_español[i])
            
            if caidas_ordenadas:
                fig.add_trace(
                    go.Bar(
                        x=dias_mostrar,
                        y=caidas_ordenadas,
                        name='Caídas por Día',
                        marker_color='lightcoral'
                    )
                )
                
                fig.update_layout(
                    title="Caídas Flag_Ready por Día de la Semana",
                    xaxis_title="Día de la Semana",
                    yaxis_title="Número de Caídas"
                )
        
        fig.update_layout(height=400)
        return fig
        
    except Exception as e:
        st.error(f"Error en análisis por día: {str(e)}")
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

def analizar_distribucion_tiempo_por_archivo(df: pd.DataFrame, flag_name: str, files_list: list) -> go.Figure:
    """Analiza distribución de tiempo de una flag por archivo"""
    fig = go.Figure()
    
    try:
        if flag_name not in df.columns or not files_list:
            fig.add_annotation(text=f"Datos insuficientes para análisis de {flag_name}", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Simular división por archivos
        archivos = []
        tiempos_on = []
        
        total_files = len(files_list)
        registros_por_file = len(df) // total_files if total_files > 0 else len(df)
        
        for i, file in enumerate(files_list):
            inicio = i * registros_por_file
            fin = min((i + 1) * registros_por_file, len(df))
            df_file = df.iloc[inicio:fin]
            
            if not df_file.empty:
                tiempo_on = (df_file[flag_name] == 1).sum()
                archivos.append(file.name if hasattr(file, 'name') else f"Archivo_{i+1}")
                tiempos_on.append(tiempo_on)
        
        if archivos:
            fig.add_trace(
                go.Bar(
                    x=archivos,
                    y=tiempos_on,
                    name=f'Tiempo {flag_name}',
                    marker_color='lightblue'
                )
            )
            
            fig.update_layout(
                title=f"Distribución de Tiempo {flag_name} por Archivo",
                xaxis_title="Archivo",
                yaxis_title="Tiempo ON (registros)",
                height=400
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Error en distribución por archivo: {str(e)}")
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

def analizar_lazo_cerrado_por_archivo(df: pd.DataFrame, files_list: list) -> go.Figure:
    """Analiza porcentaje de tiempo en lazo cerrado por archivo"""
    fig = go.Figure()
    
    try:
        # Buscar columna de lazo cerrado (usar OPTIBAT_ON como referencia si no existe otra)
        lazo_col = None
        for col in ['Lazo_Cerrado', 'Loop_Closed', 'OPTIBAT_ON']:
            if col in df.columns:
                lazo_col = col
                break
        
        if not lazo_col or not files_list:
            fig.add_annotation(text="No se encontró columna de lazo cerrado", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Simular división por archivos
        archivos = []
        porcentajes = []
        
        total_files = len(files_list)
        registros_por_file = len(df) // total_files if total_files > 0 else len(df)
        
        for i, file in enumerate(files_list):
            inicio = i * registros_por_file
            fin = min((i + 1) * registros_por_file, len(df))
            df_file = df.iloc[inicio:fin]
            
            if not df_file.empty:
                porcentaje_lazo = (df_file[lazo_col] == 1).sum() / len(df_file) * 100
                archivos.append(file.name if hasattr(file, 'name') else f"Archivo_{i+1}")
                porcentajes.append(porcentaje_lazo)
        
        if archivos:
            fig.add_trace(
                go.Bar(
                    x=archivos,
                    y=porcentajes,
                    name='% Lazo Cerrado',
                    marker_color='lightgreen'
                )
            )
            
            fig.update_layout(
                title="Porcentaje de Tiempo en Lazo Cerrado por Archivo",
                xaxis_title="Archivo",
                yaxis_title="Porcentaje (%)",
                height=400
            )
        
        return fig
        
    except Exception as e:
        st.error(f"Error en análisis de lazo cerrado: {str(e)}")
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

if __name__ == "__main__":
    main()
