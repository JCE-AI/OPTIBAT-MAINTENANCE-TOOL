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

# Simple Authentication

# Graph / SharePoint
import requests
import msal

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
# SIMPLE AUTHENTICATION MODULE
# =========================
def check_authentication():
    """Simple authentication using secrets or session state"""
    
    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        return True, st.session_state.get('user_name', 'Usuario')
    
    # Default credentials for development  
    default_users = {
        "Administrador": {"password": "admin123", "name": "Administrador"},
        "demo": {"password": "demo123", "name": "Usuario Demo"}
    }
    
    users = default_users
    
    return False, users

def show_simple_login():
    """Show clean and simple login form"""
    
    # Header Section - Simple
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem; background: linear-gradient(135deg, #E31E32 0%, #CC1A2C 100%); 
                border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h1 style="font-size: 3.5rem; margin: 0; font-weight: 900;">🚀 OPTIMITIVE</h1>
        <div style="height: 3px; width: 60px; background: white; margin: 1rem auto; border-radius: 2px;"></div>
        <h2 style="font-size: 1.5rem; margin: 0; font-weight: 300;">Monthly Report Generator</h2>
        <p style="margin: 1rem 0 0 0; opacity: 0.9;">Professional SharePoint Integration & Flag Analysis Tool</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login Form Section
    st.markdown("## 🔐 Iniciar Sesión")
    st.markdown("Accede al sistema de reportes mensual")
    
    # Custom CSS for better form styling
    st.markdown("""
    <style>
    .stTextInput > div > div > input {
        padding: 1rem !important;
        font-size: 1.1rem !important;
        border: 2px solid #DEE2E6 !important;
        border-radius: 10px !important;
        background: #F8F9FA !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E31E32 !important;
        box-shadow: 0 0 0 2px rgba(227, 30, 50, 0.2) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #E31E32 0%, #CC1A2C 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.8rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("🔐 Contraseña", type="password", placeholder="Ingrese su contraseña")
            submit = st.form_submit_button("🚀 Iniciar Sesión")
            
            if submit:
                authenticated, users = check_authentication()
                
                if username in users and users[username]["password"] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['user_name'] = users[username]["name"]
                    st.session_state['username'] = username
                    st.success("✅ Acceso autorizado. Redirigiendo...")
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    
    # Help section (without showing credentials)
    st.markdown("---")
    with st.expander("ℹ️ ¿Necesitas ayuda?"):
        st.markdown("""
        **Para obtener acceso al sistema:**
        - Contacta al administrador para recibir tus credenciales
        - Las credenciales son confidenciales y personales
        
        **Características del sistema:**
        - 📊 Análisis avanzado de flags
        - 📈 Generación de reportes profesionales
        - 💾 Exportación en múltiples formatos
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
    
    # File uploaders
    st.markdown("### 📤 Subir Archivos para Análisis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 Archivos SampleFiles (.osf)")
        sample_files = st.file_uploader(
            "Seleccione archivos .osf",
            type=['osf'],
            accept_multiple_files=True,
            key="sample_files"
        )
        
        if sample_files:
            st.success(f"✅ {len(sample_files)} archivo(s) .osf seleccionado(s)")
            for file in sample_files:
                st.write(f"📄 {file.name}")
    
    with col2:
        st.markdown("#### 📊 Archivos Statistics (.txt)")
        stats_files = st.file_uploader(
            "Seleccione archivos .txt", 
            type=['txt'],
            accept_multiple_files=True,
            key="stats_files"
        )
        
        if stats_files:
            st.success(f"✅ {len(stats_files)} archivo(s) .txt seleccionado(s)")
            for file in stats_files:
                st.write(f"📊 {file.name}")
    
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
            analyze_local_files(sample_files, stats_files, project_type, month_name, notes)
    
    else:
        st.info("👆 Seleccione al menos un archivo para comenzar el análisis")
    
    # Back to main page
    st.markdown("---")
    if st.button("🏠 Volver al Inicio", use_container_width=True):
        if 'local_mode' in st.session_state:
            del st.session_state['local_mode']
        st.rerun()

def analyze_local_files(sample_files, stats_files, project_type, month_name, notes):
    """Analyze uploaded local files"""
    
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
            
            with st.expander("🔍 Análisis Detallado", expanded=False):
                st.dataframe(
                    df_analysis,
                    use_container_width=True,
                    hide_index=True
                )
            
            # Generate reports
            st.markdown("### 💾 Descargar Reportes")
            
            detected_project = df_analysis["Project"].iloc[0] if not df_analysis.empty else project_type
            
            # HTML Report
            html_report = generate_html_report(
                month_name,
                detected_project,
                stats,
                df_analysis,
                notes
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📄 Descargar HTML",
                    data=html_report,
                    file_name=f"Local_Report_{month_name}.html",
                    mime="text/html",
                    use_container_width=True
                )
            
            with col2:
                # CSV Export
                import io
                csv_buffer = io.StringIO()
                df_analysis.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="📊 Descargar CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"Local_Report_{month_name}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        except Exception as e:
            st.error(f"❌ Error al analizar archivos: {str(e)}")
            with st.expander("Ver detalles del error"):
                st.code(traceback.format_exc())

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
# MAIN APPLICATION
# =========================
def main():
    # Simple authentication check
    authenticated, user_info = check_authentication()
    
    if not authenticated:
        show_simple_login()
        st.stop()
    
    # Get user name for display
    user_name = st.session_state.get('user_name', 'Usuario')
    
    # Header with user info and logout
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"""
        <div class="main-header">
            <div class="brand-title">OPTIMITIVE</div>
            <div class="brand-subtitle">Monthly Report Generator | SharePoint Integration</div>
            <div style="margin-top: 1rem; font-size: 1rem;">
                👤 Usuario: <strong>{user_name}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("")  # Spacer
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
                    padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0;">📁 SELECCIONAR ARCHIVOS</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Always use local files - no SharePoint dependency
        if st.button("📂 Buscar Archivos en PC", use_container_width=True, type="primary"):
            st.session_state['local_mode'] = True
            st.success("✅ Selector de archivos activado")
            st.rerun()
        
        st.info("💡 Selecciona archivos .osf y .txt de tu computadora para generar reportes")
        
        st.markdown("---")
        
        # Analysis options
        st.subheader("📊 Opciones de Análisis")
        
        project_type = st.selectbox(
            "Tipo de Proyecto",
            ["Auto", "CEMEX", "RCC"],
            help="Auto detectará el tipo basándose en las columnas del archivo",
            key="sharepoint_project_type"
        )
        
        include_stats = st.checkbox(
            "Incluir carpeta Statistics",
            value=True,
            help="Analizar archivos en la carpeta Statistics"
        )
        
        include_samples = st.checkbox(
            "Incluir carpeta SampleFiles",
            value=True,
            help="Analizar archivos en la carpeta SampleFiles"
        )
        
        st.markdown("---")
        
        # Info section
        with st.expander("ℹ️ Información"):
            st.markdown(f"""
            **Versión:** 1.0.0
            
            **Flags CEMEX:**
            - OPTIBAT_ON
            - Flag_Ready
            - Communication_ECS
            - Support_Flag_Copy
            - Macrostates_Flag_Copy
            - Resultexistance_Flag_Copy
            - OPTIBAT_WATCHDOG
            
            **Flags RCC:**
            - OPTIBAT_ON
            - MacroState_flag
            - Support
            - ResulExistance_Quality_flag
            - OPTIBAT_COMMUNICATION
            """)
    
    # Main content - Always use local files
    if st.session_state.get('local_mode', False):
        show_local_file_browser()
    else:
        # Show welcome message with instructions
        st.markdown("### 🏠 Bienvenido al Generador de Reportes")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['accent_blue']} 0%, #0077AA 100%); 
                    color: white; padding: 2rem; border-radius: 15px; text-align: center; margin: 2rem 0;">
            <h3 style="margin: 0 0 1rem 0;">📊 Sistema de Análisis de Flags</h3>
            <p style="margin: 0; font-size: 1.1rem;">
                Herramienta profesional para análisis de archivos .osf y .txt<br>
                Genera reportes completos con visualizaciones y estadísticas
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Features overview
        st.markdown("### ✨ Características")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 1.5rem; border-radius: 15px; text-align: center; height: 200px;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <h4 style="color: {OPTIMITIVE_COLORS['text_primary']}; margin: 0.5rem 0;">Análisis Automático</h4>
                <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; font-size: 0.9rem;">
                    Detección inteligente de flags CEMEX y RCC con estadísticas completas
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 1.5rem; border-radius: 15px; text-align: center; height: 200px;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                <h4 style="color: {OPTIMITIVE_COLORS['text_primary']}; margin: 0.5rem 0;">Visualizaciones</h4>
                <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; font-size: 0.9rem;">
                    Gráficos interactivos y dashboards profesionales para análisis visual
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: {OPTIMITIVE_COLORS['medium_bg']}; padding: 1.5rem; border-radius: 15px; text-align: center; height: 200px;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💾</div>
                <h4 style="color: {OPTIMITIVE_COLORS['text_primary']}; margin: 0.5rem 0;">Reportes</h4>
                <p style="color: {OPTIMITIVE_COLORS['text_secondary']}; font-size: 0.9rem;">
                    Exportación en HTML, CSV y PDF para compartir resultados
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 🚀 Comenzar")
        st.info("👈 Usa el botón **'📂 Buscar Archivos en PC'** en la barra lateral para comenzar el análisis")
        
        # Supported files info
        with st.expander("📋 Tipos de Archivo Soportados"):
            st.markdown("""
            **📄 SampleFiles (.osf):**
            - Archivos con datos de muestra
            - Contienen información de flags y variables
            
            **📊 Statistics (.txt):**
            - Archivos de estadísticas
            - Datos complementarios para el análisis
            
            **🎯 Flags Soportados:**
            - **CEMEX:** OPTIBAT_ON, Flag_Ready, Communication_ECS, Support_Flag_Copy, etc.
            - **RCC:** OPTIBAT_ON, MacroState_flag, Support, ResulExistance_Quality_flag, etc.
            """)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <h3 style="color: #E31E32; margin-bottom: 1rem;">OPTIMITIVE</h3>
        <p><strong>© 2024 Optimitive | AI Optimization Solutions</strong></p>
        <p>🌐 <a href="https://optimitive.com" target="_blank" style="color: #E31E32;">optimitive.com</a></p>
        <p><strong>Developed by Juan Cruz E.</strong> | Monthly Report Generator v1.0.0</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()