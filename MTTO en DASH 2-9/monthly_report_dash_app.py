"""
Monthly Report Generator - Optimitive Edition (DASH VERSION)
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

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Scipy para análisis avanzado
try:
    from scipy.interpolate import UnivariateSpline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Graph / SharePoint
import requests
import msal
import pytz
import logging

# PDF/HTML helpers
from bs4 import BeautifulSoup
try:
    from weasyprint import HTML as WEASY_HTML
    WEASY_AVAILABLE = True
except Exception:
    WEASY_AVAILABLE = False

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
        excel_path = os.path.join(os.path.dirname(__file__), "..", "STATISTICS FLAGS", "INFORME_FLAGS_CLIENTES-tomardeaqui.xlsx")
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

# =========================
# UTILITY FUNCTIONS
# =========================

def detect_client_flag_columns(df_columns: list) -> dict:
    """Detecta automáticamente las columnas de flags del cliente"""
    detected = {}
    
    for standard_flag, variations in FLAG_VARIATIONS.items():
        for variation in variations:
            if variation in df_columns:
                detected[standard_flag] = variation
                break
    
    return detected

def get_standardized_columns(df: pd.DataFrame, detected_mapping: dict = None) -> dict:
    """Obtiene columnas estandarizadas con nombres legibles"""
    if detected_mapping is None:
        detected_mapping = detect_client_flag_columns(df.columns.tolist())
    
    standardized = {}
    
    readable_names = {
        "OPTIBAT_ON": "Sistema OPTIBAT Activo",
        "Flag_Ready": "Sistema Listo", 
        "Communication_ECS": "Comunicación ECS",
        "Support_Flag_Copy": "Flag de Soporte",
        "Macrostates_Flag_Copy": "Estados Macro",
        "Resultexistance_Flag_Copy": "Existencia de Resultados",
        "OPTIBAT_WATCHDOG": "Monitor OPTIBAT"
    }
    
    for standard_flag, client_column in detected_mapping.items():
        if client_column in df.columns:
            readable_name = readable_names.get(standard_flag, standard_flag)
            standardized[readable_name] = client_column
    
    return standardized

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

# =========================
# DATA PROCESSING FUNCTIONS
# =========================

def load_and_process_files(uploaded_files_content) -> pd.DataFrame:
    """Process uploaded files and return consolidated DataFrame"""
    dfs = []
    errors = []
    
    for file_content, filename in uploaded_files_content:
        try:
            # Read file content
            content = base64.b64decode(file_content.split(',')[1]).decode('utf-8')
            
            # Detect separator
            lines = content.split('\n')[:5]
            if any('\t' in line for line in lines):
                separator = '\t'
            elif any(';' in line for line in lines):
                separator = ';'
            else:
                separator = ','
            
            # Read as DataFrame
            df = pd.read_csv(io.StringIO(content), sep=separator, encoding='utf-8')
            
            # Clean column names
            df.columns = [col.strip() for col in df.columns]
            
            # Convert Date column if present
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Add source file column
            df['source_file'] = filename
            
            dfs.append(df)
            
        except Exception as e:
            errors.append(f"Error en {filename}: {str(e)}")
    
    if not dfs:
        raise ValueError("No se pudo procesar ningún archivo")
    
    # Concatenate all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True, sort=False)
    
    # Sort by date if available
    if 'Date' in combined_df.columns:
        combined_df = combined_df.sort_values('Date', na_position='last')
    
    return combined_df

# =========================
# VISUALIZATION FUNCTIONS
# =========================

def create_ready_evolution_chart(df: pd.DataFrame) -> go.Figure:
    """Gráfico 1: Evolución del Porcentaje de Tiempo en OPTIBAT_READY=1"""
    fig = go.Figure()
    
    try:
        # Buscar columna OPTIBAT_READY / Flag_Ready
        ready_col = None
        for col in ['Flag_Ready', 'OPTIBAT_READY', 'Ready']:
            if col in df.columns:
                ready_col = col
                break
        
        if ready_col is None or 'Date' not in df.columns:
            fig.add_annotation(text="Datos insuficientes: Se requiere columna Ready y Date", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Agrupar por día y calcular porcentaje
        df_temp = df.copy()
        df_temp['Fecha'] = pd.to_datetime(df_temp['Date']).dt.date
        
        daily_ready = df_temp.groupby('Fecha').agg({
            ready_col: ['count', 'sum']
        }).reset_index()
        
        daily_ready.columns = ['Fecha', 'Total', 'Ready_Count']
        daily_ready['Porcentaje_Ready'] = (daily_ready['Ready_Count'] / daily_ready['Total'] * 100)
        
        # Crear gráfico de línea
        fig.add_trace(
            go.Scatter(
                x=daily_ready['Fecha'],
                y=daily_ready['Porcentaje_Ready'],
                mode='lines+markers',
                name='% OPTIBAT_READY=1',
                line=dict(color='#FF6B47', width=3),
                marker=dict(size=8, color='#FF6B47'),
                hovertemplate='<b>Fecha:</b> %{x}<br><b>Porcentaje:</b> %{y:.1f}%<extra></extra>'
            )
        )
        
        fig.update_layout(
            title=dict(text="Evolución del Porcentaje de Tiempo en OPTIBAT_READY=1", font_size=20),
            xaxis_title="Fecha",
            yaxis_title="Porcentaje (%)",
            height=750,
            font=dict(size=16),
            xaxis=dict(title_font_size=18, tickfont_size=14),
            yaxis=dict(range=[0, 105], title_font_size=18, tickfont_size=14),
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

def create_closed_loop_evolution_chart(df: pd.DataFrame) -> go.Figure:
    """Gráfico 2: Evolución del Porcentaje del Tiempo en Lazo Cerrado (OPTIBAT_ON=1)"""
    fig = go.Figure()
    
    try:
        # Buscar columna OPTIBAT_ON
        on_col = None
        for col in ['OPTIBAT_ON', 'ON']:
            if col in df.columns:
                on_col = col
                break
        
        if on_col is None or 'Date' not in df.columns:
            fig.add_annotation(text="Datos insuficientes: Se requiere columna ON y Date", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Agrupar por día y calcular porcentaje
        df_temp = df.copy()
        df_temp['Fecha'] = pd.to_datetime(df_temp['Date']).dt.date
        
        daily_on = df_temp.groupby('Fecha').agg({
            on_col: ['count', 'sum']
        }).reset_index()
        
        daily_on.columns = ['Fecha', 'Total', 'ON_Count']
        daily_on['Porcentaje_ON'] = (daily_on['ON_Count'] / daily_on['Total'] * 100)
        
        # Crear gráfico de línea
        fig.add_trace(
            go.Scatter(
                x=daily_on['Fecha'],
                y=daily_on['Porcentaje_ON'],
                mode='lines+markers',
                name='% Lazo Cerrado',
                line=dict(color='#20B2AA', width=3),
                marker=dict(size=8, color='#20B2AA'),
                hovertemplate='<b>Fecha:</b> %{x}<br><b>Porcentaje:</b> %{y:.1f}%<extra></extra>'
            )
        )
        
        fig.update_layout(
            title=dict(text="Evolución del Porcentaje del Tiempo en Lazo Cerrado (OPTIBAT_ON=1)", font_size=20),
            xaxis_title="Fecha",
            yaxis_title="Porcentaje (%)",
            height=750,
            font=dict(size=16),
            xaxis=dict(title_font_size=18, tickfont_size=14),
            yaxis=dict(range=[0, 105], title_font_size=18, tickfont_size=14),
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        fig.add_annotation(text=f"Error: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

def create_timeline_chart(df: pd.DataFrame, available_flags: list = None) -> go.Figure:
    """Timeline del sistema mostrando todos los flags disponibles"""
    if available_flags is None:
        available_flags = MAIN_FLAGS
    
    fig = go.Figure()
    
    try:
        if 'Date' not in df.columns:
            fig.add_annotation(text="No hay columna 'Date' disponible para timeline", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig
        
        # Color palette expandida para más flags
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD',
                 '#00D2D3', '#FF9F43', '#EE5A24', '#0AD3FF', '#575FCF', '#222F3E', '#26DE81', '#FC427B',
                 '#FD79A8', '#6C5CE7', '#A29BFE', '#74B9FF', '#00B894', '#00CEC9', '#55A3FF', '#FD79A8']
        
        color_idx = 0
        flags_added = 0
        
        for flag in available_flags:
            if flag in df.columns and not df[flag].dropna().empty:
                # Usar el flag como está (nombre del cliente)
                display_name = flag
                color = colors[color_idx % len(colors)]
                
                # Crear trace para el flag
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=df[flag] + flags_added * 1.2,  # Offset vertical
                        mode='lines',
                        name=display_name,
                        line=dict(color=color, width=2),
                        hovertemplate=f'<b>{display_name}</b><br>Tiempo: %{{x}}<br>Estado: %{{y}}<extra></extra>'
                    )
                )
                
                flags_added += 1
                color_idx += 1
        
        if flags_added == 0:
            fig.add_annotation(text="No hay flags válidos para mostrar en timeline", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        else:
            fig.update_layout(
                title=dict(text="Timeline del Sistema", font_size=20),
                xaxis_title="Tiempo",
                yaxis_title="Estado de Flags",
                height=500,
                font=dict(size=14),
                hovermode='x unified',
                showlegend=True
            )
        
        return fig
        
    except Exception as e:
        fig.add_annotation(text=f"Error en timeline: {str(e)}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

# =========================
# AUTHENTICATION
# =========================

# Simple hardcoded authentication (can be enhanced)
VALID_USERS = {
    "Administrador": "admin123",
    "demo": "demo123", 
    "optibat": "optibat2024"
}

def check_authentication(username, password):
    """Check if username and password are valid"""
    return username in VALID_USERS and VALID_USERS[username] == password

# =========================
# DASH APP INITIALIZATION
# =========================

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Optimitive Monthly Report Generator"

# =========================
# LAYOUT
# =========================

def create_login_layout():
    """Create login page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("OPTIBAT MAINTENANCE TOOL", 
                           className="text-center text-white mb-4",
                           style={'background': f'linear-gradient(135deg, {OPTIMITIVE_COLORS["primary_red"]} 0%, #B71C1C 100%)',
                                  'padding': '2rem', 'borderRadius': '15px', 'fontSize': '2.5rem'}),
                    
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("Iniciar Sesión", className="text-center mb-4"),
                            
                            dbc.Form([
                                dbc.Row([
                                    dbc.Label("Usuario", html_for="login-username"),
                                    dbc.Input(
                                        id="login-username",
                                        type="text",
                                        placeholder="Ingresa tu usuario"
                                    ),
                                ], className="mb-3"),
                                
                                dbc.Row([
                                    dbc.Label("Contraseña", html_for="login-password"),
                                    dbc.Input(
                                        id="login-password",
                                        type="password",
                                        placeholder="Ingresa tu contraseña"
                                    ),
                                ], className="mb-3"),
                                
                                dbc.Row([
                                    dbc.Button(
                                        "Iniciar Sesión",
                                        id="login-button",
                                        color="danger",
                                        size="lg",
                                        className="w-100"
                                    )
                                ], className="mb-3"),
                                
                                html.Div(id="login-alert")
                            ])
                        ])
                    ], style={'maxWidth': '500px', 'margin': '0 auto'})
                ])
            ], width=12)
        ])
    ], fluid=True, className="vh-100 d-flex align-items-center", 
       style={'background': OPTIMITIVE_COLORS['medium_bg']})

def create_main_layout():
    """Create main application layout"""
    return dbc.Container([
        # Store components for session management
        dcc.Store(id='session-store', storage_type='session'),
        dcc.Store(id='data-store', storage_type='session'),
        
        # Header
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("OPTIBAT MAINTENANCE TOOL", className="text-center text-white mb-0")
                ], style={'background': f'linear-gradient(135deg, {OPTIMITIVE_COLORS["primary_red"]} 0%, #B71C1C 100%)',
                         'padding': '2rem', 'borderRadius': '15px', 'marginBottom': '2rem'})
            ])
        ]),
        
        # Sidebar and main content
        dbc.Row([
            # Sidebar
            dbc.Col([
                html.Div([
                    html.H3("CARGA DE DATOS", className="text-center text-white"),
                ], style={'background': f'linear-gradient(135deg, {OPTIMITIVE_COLORS["primary_red"]} 0%, #CC1A2C 100%)',
                         'padding': '1rem', 'borderRadius': '10px', 'marginBottom': '1rem'}),
                
                # File upload
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Arrastra archivos STATISTICS (.txt) aquí o ',
                        html.A('selecciona archivos')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px 0'
                    },
                    multiple=True
                ),
                
                # Upload status
                html.Div(id='upload-status'),
                
                # Client info
                html.Div(id='client-info'),
                
                # System flags info
                dbc.Accordion([
                    dbc.AccordionItem([
                        html.P("Flags Principales Monitoreados:"),
                        html.Ul([
                            html.Li("OPTIBAT_ON → Sistema principal activo"),
                            html.Li("Flag_Ready → Sistema listo para operación"), 
                            html.Li("Communication_ECS → Comunicación con ECS"),
                            html.Li("Support_Flag_Copy → Flag de soporte"),
                            html.Li("Macrostates_Flag_Copy → Estados macro"),
                            html.Li("Resultexistance_Flag_Copy → Existencia resultados"),
                            html.Li("OPTIBAT_WATCHDOG → Monitor de sistema")
                        ]),
                        html.P(f"Clientes Configurados: {len(CLIENT_FLAGS_MAPPING)}")
                    ], title="Sistema de Flags")
                ], style={'marginTop': '1rem'}),
                
                # Logout button
                html.Hr(),
                html.P(id="user-info"),
                dbc.Button("Cerrar Sesión", id="logout-button", color="secondary", className="w-100")
                
            ], width=3),
            
            # Main content
            dbc.Col([
                html.Div(id='main-content')
            ], width=9)
        ]),
        
        # Footer
        html.Footer([
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H5("OPTIMITIVE", style={'color': OPTIMITIVE_COLORS['primary_red']}),
                    html.P("© Optimitive | AI Optimization Solutions"),
                    html.P([
                        "🌐 ",
                        html.A("optimitive.com", href="https://optimitive.com", target="_blank", 
                              style={'color': OPTIMITIVE_COLORS['primary_red']})
                    ]),
                    html.P("Developed by Juan Cruz Erreguerena. | Monthly Report Generator v1.0.0")
                ], className="text-center")
            ])
        ])
        
    ], fluid=True)

# Set initial layout
app.layout = html.Div(id="app-layout")

# =========================
# CALLBACKS
# =========================

@app.callback(
    Output('app-layout', 'children'),
    Input('app-layout', 'id'),
    State('session-store', 'data')
)
def display_layout(layout_id, session_data):
    """Determine which layout to show based on authentication"""
    if session_data and session_data.get('authenticated', False):
        return create_main_layout()
    else:
        return create_login_layout()

@app.callback(
    [Output('session-store', 'data'),
     Output('login-alert', 'children')],
    Input('login-button', 'n_clicks'),
    [State('login-username', 'value'),
     State('login-password', 'value'),
     State('session-store', 'data')]
)
def handle_login(n_clicks, username, password, session_data):
    """Handle login authentication"""
    if not n_clicks:
        return session_data or {}, ""
    
    if username and password and check_authentication(username, password):
        return {'authenticated': True, 'username': username}, ""
    else:
        alert = dbc.Alert(
            "Usuario o contraseña incorrectos",
            color="danger",
            dismissable=True
        )
        return session_data or {}, alert

@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def handle_logout(n_clicks):
    """Handle logout"""
    if n_clicks:
        return {}
    return dash.no_update

@app.callback(
    [Output('data-store', 'data'),
     Output('upload-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def handle_file_upload(contents, filenames):
    """Handle file upload and processing"""
    if contents is None:
        return {}, ""
    
    try:
        # Prepare file data for processing
        uploaded_files_content = []
        for content, filename in zip(contents, filenames):
            uploaded_files_content.append((content, filename))
        
        # Process files
        df = load_and_process_files(uploaded_files_content)
        
        # Store processed data
        data_store = {
            'df': df.to_dict('records'),
            'columns': df.columns.tolist(),
            'shape': df.shape
        }
        
        status = dbc.Alert(
            f"✅ Cargados {len(filenames)} archivo(s) correctamente - {df.shape[0]:,} registros",
            color="success"
        )
        
        return data_store, status
        
    except Exception as e:
        error_alert = dbc.Alert(
            f"❌ Error procesando archivos: {str(e)}",
            color="danger"
        )
        return {}, error_alert

@app.callback(
    [Output('client-info', 'children'),
     Output('user-info', 'children')],
    [Input('data-store', 'data'),
     Input('session-store', 'data')]
)
def update_client_info(data_store, session_data):
    """Update client information and user display"""
    client_info = ""
    user_info = ""
    
    if session_data and session_data.get('authenticated'):
        username = session_data.get('username', 'Usuario')
        user_info = f"Usuario: {username}"
        
        if data_store and 'columns' in data_store:
            detected_client = detect_client_from_flags(data_store['columns'])
            available_flags = get_available_flags_in_data(pd.DataFrame(data_store['df']))
            
            client_info = dbc.Card([
                dbc.CardBody([
                    html.H6("INFORMACIÓN DEL CLIENTE", className="card-title"),
                    html.P(f"Cliente: {detected_client}", className="card-text"),
                    html.P(f"Flags activos: {len(available_flags)}/{len(MAIN_FLAGS)}", className="card-text"),
                    html.P(f"Registros: {data_store['shape'][0]:,}", className="card-text")
                ])
            ], style={'marginTop': '1rem'})
    
    return client_info, user_info

@app.callback(
    Output('main-content', 'children'),
    Input('data-store', 'data'),
    prevent_initial_call=True
)
def update_main_content(data_store):
    """Update main dashboard content"""
    if not data_store or 'df' not in data_store:
        return dbc.Card([
            dbc.CardBody([
                html.H3("👋 Bienvenido", className="text-center"),
                html.P("👈 Carga archivos STATISTICS en la barra lateral para comenzar el análisis", 
                      className="text-center"),
                html.Hr(),
                html.H5("🎯 Funcionalidades"),
                html.Ul([
                    html.Li("✅ Detección automática de cliente por flags"),
                    html.Li(f"✅ Análisis de {len(MAIN_FLAGS)} flags principales"),
                    html.Li("✅ Dashboards interactivos con KPIs"),
                    html.Li(f"✅ Soporte para {len(CLIENT_FLAGS_MAPPING)} configuraciones de cliente")
                ])
            ])
        ])
    
    # Process stored data
    df = pd.DataFrame(data_store['df'])
    detected_client = detect_client_from_flags(data_store['columns'])
    available_flags = get_available_flags_in_data(df)
    
    # Create main dashboard
    return html.Div([
        # KPI Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("CLIENTE", className="card-title text-center text-white"),
                        html.H3(detected_client, className="text-center text-white")
                    ])
                ], style={'background': OPTIMITIVE_COLORS['success'], 'color': 'white'})
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("FLAGS ACTIVOS", className="card-title text-center text-white"),
                        html.H3(f"{len(available_flags)}/{len(MAIN_FLAGS)}", className="text-center text-white")
                    ])
                ], style={'background': OPTIMITIVE_COLORS['accent_blue'], 'color': 'white'})
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("REGISTROS", className="card-title text-center text-white"),
                        html.H3(f"{len(df):,}", className="text-center text-white")
                    ])
                ], style={'background': OPTIMITIVE_COLORS['warning'], 'color': 'white'})
            ], width=4)
        ], className="mb-4"),
        
        # Charts section
        html.Hr(),
        
        # Timeline del Sistema
        dbc.Card([
            dbc.CardHeader(html.H4("Timeline del Sistema")),
            dbc.CardBody([
                dcc.Graph(
                    id='timeline-chart',
                    figure=create_timeline_chart(df, available_flags)
                )
            ])
        ], className="mb-4"),
        
        # Evolution Charts
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Evolución OPTIBAT_READY")),
                    dbc.CardBody([
                        dcc.Graph(
                            id='ready-evolution-chart',
                            figure=create_ready_evolution_chart(df)
                        )
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Evolución Lazo Cerrado")),
                    dbc.CardBody([
                        dcc.Graph(
                            id='closed-loop-evolution-chart', 
                            figure=create_closed_loop_evolution_chart(df)
                        )
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Data Table
        dbc.Card([
            dbc.CardHeader(html.H4("Vista de Datos")),
            dbc.CardBody([
                dash_table.DataTable(
                    id='data-table',
                    data=df.head(100).to_dict('records'),
                    columns=[{"name": col, "id": col} for col in df.columns],
                    page_size=20,
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'fontSize': '12px'},
                    style_header={'backgroundColor': OPTIMITIVE_COLORS['primary_red'], 'color': 'white'}
                )
            ])
        ])
    ])

# =========================
# RUN APP
# =========================

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8082)