"""
Monthly Report Generator - Enhanced Optimitive Edition
Professional SharePoint Integration & Advanced OPTIBAT Analytics
Developed by Juan Cruz E. | Powered by Optimitive
Version 2.0 - Enhanced with Real-time Dashboard
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
import pytz
import logging

# Simple Authentication
import requests
import msal

# PDF/HTML helpers
from bs4 import BeautifulSoup
try:
    from weasyprint import HTML as WEASY_HTML
    WEASY_AVAILABLE = True
except Exception:
    WEASY_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# METRICS & ACCESS LOGGING
# =========================
def get_ip():
    """Get client IP address"""
    try:
        if hasattr(st, "request") and hasattr(st.request, "headers"):
            ip = st.request.headers.get('X-Forwarded-For', None)
            if ip:
                ip = ip.split(',')[0].strip()
            return ip or "Unknown"
        return "Unknown"
    except Exception:
        return "Unknown"

def log_access(ip):
    """Log access to Google Sheets"""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
        
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
        logger.warning(f"Could not log metrics to Google Sheets: {e}")
        pass 

# Initialize access logging
if 'access_logged' not in st.session_state:
    st.session_state['access_logged'] = True
    user_ip = get_ip()
    log_access(user_ip)

# =========================
# CONFIGURATION & THEME
# =========================
OPTIMITIVE_COLORS = {
    'primary_red': '#E31E32',
    'primary_black': '#000000',
    'dark_bg': '#FFFFFF',
    'medium_bg': '#F8F9FA',
    'light_bg': '#FFFFFF',
    'accent_blue': '#0099CC',
    'text_primary': '#2C3E50',
    'text_secondary': '#6C757D',
    'success': '#28A745',
    'warning': '#FFC107',
    'error': '#DC3545',
    'border': '#DEE2E6'
}

# OPTIBAT Dashboard Constants
MAIN_FLAGS = [
    "OPTIBAT_ON", "Flag_Ready", "Communication_ECS", "FM1_COMMS_HeartBeat",
    "Support_Flag_Copy", "Macrostates_Flag_Copy", "Resultexistance_Flag_Copy", "OPTIBAT_WATCHDOG"
]

FLAG_DESCRIPTIONS = {
    "OPTIBAT_ON": "Sistema principal activo",
    "Flag_Ready": "Sistema listo para operación",
    "Communication_ECS": "Comunicación con ECS",
    "FM1_COMMS_HeartBeat": "Latido del sistema FM1",
    "Support_Flag_Copy": "Flag de soporte",
    "Macrostates_Flag_Copy": "Estados macro del sistema",
    "Resultexistance_Flag_Copy": "Existencia de resultados",
    "OPTIBAT_WATCHDOG": "Monitor de sistema"
}

PULSING_SIGNALS_FOR_GAUGE = ["FM1_COMMS_HeartBeat", "Communication_ECS", "OPTIBAT_WATCHDOG"]

COLOR_SCHEME = {
    'primary': '#3498db', 'success': '#27ae60', 'warning': '#f39c12',
    'danger': '#e74c3c', 'info': '#3498db', 'dark': '#2c3e50', 'light': '#ecf0f1'
}

st.set_page_config(
    page_title="Optimitive Analytics Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# ENHANCED AUTHENTICATION
# =========================
def check_authentication():
    """Enhanced authentication with multiple user support"""
    
    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        return True, st.session_state.get('user_name', 'Usuario')
    
    # Get auth config from secrets
    auth_config = st.secrets.get("auth", {})
    
    # Default credentials for development
    default_users = {
        "Administrador": {"password": "admin123", "name": "Administrador", "role": "admin"},
        "demo": {"password": "demo123", "name": "Usuario Demo", "role": "user"},
        "optibat": {"password": "optibat2024", "name": "OPTIBAT Analyst", "role": "analyst"}
    }
    
    # Use secrets or default
    users = auth_config.get("users", default_users)
    
    return False, users

def show_enhanced_login():
    """Show enhanced login form with role-based access"""
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
                padding: 3rem 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; color: white;">
        <h1 style="font-size: 3.5rem; margin: 0; font-weight: 900;">🚀 OPTIMITIVE ANALYTICS</h1>
        <div style="height: 3px; width: 80px; background: white; margin: 1rem auto; border-radius: 2px;"></div>
        <h2 style="font-size: 1.5rem; margin: 0; font-weight: 300;">Enhanced Report Generator & OPTIBAT Dashboard</h2>
        <p style="margin: 1rem 0 0 0; opacity: 0.9;">Professional SharePoint Integration & Real-time Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🔐 Sistema de Acceso")
        
        with st.form("enhanced_login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("🔐 Contraseña", type="password", placeholder="Ingrese su contraseña")
            submit = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
            
            if submit:
                authenticated, users = check_authentication()
                
                if username in users and users[username]["password"] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['user_name'] = users[username]["name"]
                    st.session_state['user_role'] = users[username].get("role", "user")
                    st.session_state['username'] = username
                    st.success("✅ Acceso autorizado. Cargando sistema...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")

# =========================
# OPTIBAT METRICS ANALYZER
# =========================
class OptibatMetricsAnalyzer:
    def __init__(self):
        self.df_processed = pd.DataFrame()

    @staticmethod
    @st.cache_data
    def load_and_process_files(uploaded_files) -> pd.DataFrame:
        """Load and process OPTIBAT data files"""
        dfs = []
        errors = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, file in enumerate(uploaded_files):
            try:
                status_text.text(f"Procesando archivo {idx + 1}/{len(uploaded_files)}: {file.name}")
                
                # Read headers
                headers = pd.read_csv(file, sep='\t', skiprows=1, nrows=1, header=None, encoding='latin1').iloc[0].tolist()
                file.seek(0)
                
                # Handle duplicate headers
                seen = {}
                names = []
                for h in headers:
                    if h in seen:
                        seen[h] += 1
                        names.append(f"{h}_{seen[h]}")
                    else:
                        seen[h] = 0
                        names.append(h)
                
                # Read data
                df_temp = pd.read_csv(file, sep='\t', skiprows=10, header=None, names=names, engine='python', encoding='latin1')
                
                # Process datetime
                if "Date" in df_temp.columns:
                    df_temp["Date"] = pd.to_datetime(df_temp["Date"], errors='coerce')
                    df_temp = df_temp.dropna(subset=['Date'])
                
                # Convert flag columns to numeric
                for flag_col in MAIN_FLAGS:
                    if flag_col in df_temp.columns:
                        df_temp[flag_col] = pd.to_numeric(df_temp[flag_col], errors='coerce')
                
                df_temp['source_file'] = file.name 
                dfs.append(df_temp)
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
            except Exception as e:
                logger.error(f"Error processing file {file.name}: {str(e)}")
                errors.append(f"Error en {file.name}: {str(e)}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if not dfs:
            raise ValueError("No se pudieron procesar los archivos o no contienen datos válidos.")
        
        df_combined = pd.concat(dfs, ignore_index=True)
        df_combined = df_combined.sort_values('Date', ascending=True).reset_index(drop=True)
        
        return df_combined

    def calculate_heartbeat_health(self, df: pd.DataFrame, hb_column: str, hours_window: int = 2) -> str:
        """Calculate heartbeat signal health status"""
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
        
        # Check for stuck signal
        unique_vals = hb_signal.nunique()
        if unique_vals == 1:
            return f"🔴 Señal Pegada ({hb_signal.iloc[0]})"
        
        # Calculate pulse rate
        transitions = (hb_signal.diff() != 0).sum()
        total_minutes = len(hb_signal) / 60 if len(hb_signal) > 60 else len(hb_signal)
        pulse_rate = transitions / total_minutes if total_minutes > 0 else 0
        
        if pulse_rate > 0.5:
            return f"🟢 Activo ({pulse_rate:.1f}/min)"
        elif pulse_rate > 0.1:
            return f"🟡 Lento ({pulse_rate:.1f}/min)"
        else:
            return f"🔴 Inactivo ({pulse_rate:.1f}/min)"

    def generate_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive KPIs for OPTIBAT system"""
        if df.empty:
            return {}
        
        kpis = {}
        
        # Overall system status
        if "OPTIBAT_ON" in df.columns:
            optibat_on = df["OPTIBAT_ON"].dropna()
            if not optibat_on.empty:
                uptime_pct = (optibat_on.mean() * 100) if len(optibat_on) > 0 else 0
                kpis['system_uptime'] = uptime_pct
        
        # Communication health
        comm_flags = ["Communication_ECS", "FM1_COMMS_HeartBeat"]
        comm_health = []
        for flag in comm_flags:
            if flag in df.columns:
                flag_data = df[flag].dropna()
                if len(flag_data) > 0:
                    health = flag_data.mean() * 100
                    comm_health.append(health)
        
        kpis['communication_health'] = np.mean(comm_health) if comm_health else 0
        
        # Data quality
        total_records = len(df)
        valid_records = len(df.dropna())
        kpis['data_quality'] = (valid_records / total_records * 100) if total_records > 0 else 0
        
        # Alert count (flags at 0 when they should be 1)
        alert_count = 0
        critical_flags = ["OPTIBAT_ON", "Flag_Ready"]
        for flag in critical_flags:
            if flag in df.columns:
                flag_data = df[flag].dropna()
                if len(flag_data) > 0:
                    alert_count += (flag_data == 0).sum()
        
        kpis['alert_count'] = alert_count
        
        return kpis

# =========================
# LEGACY FLAG ANALYSIS
# =========================
FLAG_DEFINITIONS = {
    "CEMEX": [
        "OPTIBAT_ON", "Flag_Ready", "Communication_ECS",
        "Support_Flag_Copy", "Macrostates_Flag_Copy",
        "Resultexistance_Flag_Copy", "OPTIBAT_WATCHDOG"
    ],
    "RCC": [
        "OPTIBAT_ON", "MacroState_flag", "Support",
        "ResulExistance_Quality_flag", "OPTIBAT_COMMUNICATION"
    ]
}

def parse_header_line(line: str) -> List[str]:
    """Parse header line with multiple possible delimiters"""
    line = line.strip().strip("\ufeff")
    
    if "\t" in line:
        columns = line.split("\t")
    else:
        columns = re.split(r"\s{2,}", line)
    
    return [col.strip().strip('"').strip("'") for col in columns if col.strip()]

def extract_varname_header(content: bytes) -> List[str]:
    """Extract VarName header from file content"""
    try:
        text = content.decode("utf-8-sig", errors="replace")
        lines = text.splitlines()
        
        for line in lines[:100]:
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
    
    cemex_indicators = {
        "flag_ready", "communication_ecs", "support_flag_copy",
        "macrostates_flag_copy", "resultexistance_flag_copy"
    }
    
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
    
    if project_type == "Auto":
        for category, files in files_data.items():
            if files and not detected_project:
                _, content = files[0]
                header = extract_varname_header(content)
                detected_project = detect_project_type(header)
        
        if not detected_project:
            detected_project = "CEMEX"
    else:
        detected_project = project_type
    
    flags = FLAG_DEFINITIONS.get(detected_project, FLAG_DEFINITIONS["CEMEX"])
    
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
# VISUALIZATION FUNCTIONS
# =========================
def create_gauge_chart(value: float, title: str, max_val: float = 100) -> go.Figure:
    """Create a gauge chart for KPI display"""
    
    # Determine color based on value
    if value >= 80:
        color = COLOR_SCHEME['success']
    elif value >= 60:
        color = COLOR_SCHEME['warning'] 
    else:
        color = COLOR_SCHEME['danger']
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'lightgray'},
                {'range': [50, 80], 'color': 'lightyellow'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def create_timeline_chart(df: pd.DataFrame, flags: List[str]) -> go.Figure:
    """Create timeline chart showing flag states over time"""
    
    fig = make_subplots(
        rows=len(flags), cols=1,
        shared_xaxes=True,
        subplot_titles=flags,
        vertical_spacing=0.05
    )
    
    for i, flag in enumerate(flags):
        if flag in df.columns and "Date" in df.columns:
            flag_data = df[["Date", flag]].dropna()
            if not flag_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=flag_data["Date"],
                        y=flag_data[flag],
                        mode='lines',
                        name=flag,
                        line=dict(color=COLOR_SCHEME['primary'], width=2),
                        fill='tonexty' if flag_data[flag].mean() > 0.5 else None
                    ),
                    row=i+1, col=1
                )
    
    fig.update_layout(
        height=150*len(flags),
        title_text="Flag States Over Time",
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

# =========================
# MAIN APPLICATION MODES
# =========================
def show_optibat_dashboard(unified_files=None):
    """Show real-time OPTIBAT analytics dashboard"""
    
    st.markdown("## 📊 OPTIBAT Real-Time Dashboard")
    
    # Use unified files or allow local upload
    uploaded_files = []
    if unified_files:
        uploaded_files.extend(unified_files.get('optibat', []))
        uploaded_files.extend(unified_files.get('stats', []))
        uploaded_files.extend(unified_files.get('data', []))
    
    # Additional local upload if no unified files
    if not uploaded_files:
        st.info("💡 Upload files in the 'Data Upload Center' above, or use the uploader below:")
        local_files = st.file_uploader(
            "📤 Upload OPTIBAT Data Files (Local)",
            accept_multiple_files=True,
            type=['txt', 'csv', 'osf'],
            help="Upload TSV/CSV files from OPTIBAT system",
            key="local_optibat_files"
        )
        uploaded_files = local_files or []
    
    if uploaded_files:
        try:
            analyzer = OptibatMetricsAnalyzer()
            df = analyzer.load_and_process_files(uploaded_files)
            
            if not df.empty:
                # Generate KPIs
                kpis = analyzer.generate_kpis(df)
                
                # Display KPIs
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if 'system_uptime' in kpis:
                        fig = create_gauge_chart(kpis['system_uptime'], "System Uptime %")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'communication_health' in kpis:
                        fig = create_gauge_chart(kpis['communication_health'], "Communication Health %")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col3:
                    if 'data_quality' in kpis:
                        fig = create_gauge_chart(kpis['data_quality'], "Data Quality %")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col4:
                    st.metric(
                        "🚨 Alert Count",
                        kpis.get('alert_count', 0),
                        delta=None
                    )
                
                # Heartbeat analysis
                st.markdown("### 💓 Heartbeat Analysis")
                hb_cols = st.columns(len(PULSING_SIGNALS_FOR_GAUGE))
                
                for i, signal in enumerate(PULSING_SIGNALS_FOR_GAUGE):
                    with hb_cols[i]:
                        if signal in df.columns:
                            status = analyzer.calculate_heartbeat_health(df, signal)
                            st.metric(f"🔄 {signal}", status)
                        else:
                            st.metric(f"🔄 {signal}", "N/A")
                
                # Timeline visualization
                st.markdown("### 📈 System Timeline")
                available_flags = [flag for flag in MAIN_FLAGS if flag in df.columns]
                if available_flags:
                    selected_flags = st.multiselect(
                        "Select flags to display:",
                        available_flags,
                        default=available_flags[:4]
                    )
                    
                    if selected_flags:
                        timeline_fig = create_timeline_chart(df, selected_flags)
                        st.plotly_chart(timeline_fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 Raw Data Preview"):
                    st.dataframe(df.tail(100), use_container_width=True)
                    
        except Exception as e:
            st.error(f"Error processing OPTIBAT data: {str(e)}")
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

def show_legacy_reports(unified_files=None):
    """Show legacy monthly reports functionality"""
    
    st.markdown("## 📋 Legacy Monthly Reports")
    
    # Use unified files or allow local upload
    sample_files = []
    stats_files = []
    
    if unified_files:
        sample_files.extend(unified_files.get('optibat', []))
        sample_files.extend(unified_files.get('data', []))
        stats_files.extend(unified_files.get('stats', []))
        
        if sample_files or stats_files:
            st.success(f"📁 Using {len(sample_files)} data files and {len(stats_files)} statistics files from Upload Center")
    
    # Additional local upload if no unified files
    if not sample_files and not stats_files:
        st.info("💡 Upload files in the 'Data Upload Center' above, or use the uploaders below:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📄 SampleFiles (.osf)")
            local_sample_files = st.file_uploader(
                "Upload .osf files",
                type=['osf'],
                accept_multiple_files=True,
                key="legacy_sample_files"
            )
            sample_files = local_sample_files or []
        
        with col2:
            st.markdown("#### 📊 Statistics (.txt)")
            local_stats_files = st.file_uploader(
                "Upload .txt files", 
                type=['txt'],
                accept_multiple_files=True,
                key="legacy_stats_files"
            )
            stats_files = local_stats_files or []
    
    if sample_files or stats_files:
        # Analysis configuration
        col1, col2 = st.columns(2)
        
        with col1:
            project_type = st.selectbox(
                "Project Type",
                ["Auto", "CEMEX", "RCC"]
            )
        
        with col2:
            report_name = st.text_input(
                "Report Name",
                value="Legacy-Analysis"
            )
        
        if st.button("🚀 Generate Legacy Report", type="primary"):
            try:
                # Process files
                files_data = {"SampleFiles": [], "Statistics": []}
                
                if sample_files:
                    for file in sample_files:
                        content = file.read()
                        files_data["SampleFiles"].append((file.name, content))
                
                if stats_files:
                    for file in stats_files:
                        content = file.read()
                        files_data["Statistics"].append((file.name, content))
                
                # Analyze
                df_analysis = analyze_files(files_data, project_type)
                
                if not df_analysis.empty:
                    st.success("✅ Analysis completed successfully!")
                    
                    # Show results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Files Analyzed", df_analysis["File"].nunique())
                    with col2:
                        st.metric("Flags Checked", df_analysis["Flag"].nunique())
                    with col3:
                        coverage = df_analysis["Found"].mean() * 100
                        st.metric("Coverage", f"{coverage:.1f}%")
                    
                    # Data table
                    st.dataframe(df_analysis, use_container_width=True)
                    
                else:
                    st.warning("⚠️ No data found in uploaded files")
                    
            except Exception as e:
                st.error(f"❌ Error generating legacy report: {str(e)}")

# =========================
# MAIN APPLICATION
# =========================
def main():
    # Enhanced authentication
    authenticated, user_info = check_authentication()
    
    if not authenticated:
        show_enhanced_login()
        st.stop()
    
    user_name = st.session_state.get('user_name', 'Usuario')
    user_role = st.session_state.get('user_role', 'user')
    
    # Enhanced header with role info
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['primary_red']} 0%, #CC1A2C 100%);
                    color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
            <h1 style="margin: 0; font-size: 2.5rem; font-weight: 900;">OPTIMITIVE ANALYTICS SUITE</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">Enhanced Report Generator & Real-time OPTIBAT Dashboard</p>
            <div style="margin-top: 1rem; font-size: 1rem;">
                👤 {user_name} | 🎭 {user_role.upper()} | 🌐 {get_ip()}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("")
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main navigation
    with st.sidebar:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {OPTIMITIVE_COLORS['accent_blue']} 0%, #007AA3 100%);
                    color: white; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
            <h3 style="margin: 0;">📊 ANALYTICS SUITE</h3>
        </div>
        """, unsafe_allow_html=True)
        
        mode = st.selectbox(
            "🎯 Select Analysis Mode:",
            ["🔄 OPTIBAT Real-time Dashboard", "📋 Legacy Monthly Reports"],
            index=0
        )
        
        st.markdown("---")
        
        # Mode-specific options
        if "OPTIBAT" in mode:
            st.markdown("### ⚙️ Dashboard Settings")
            
            auto_refresh = st.checkbox("🔄 Auto Refresh", value=False)
            if auto_refresh:
                refresh_interval = st.slider("Refresh Rate (seconds)", 10, 300, 60)
                
            show_advanced = st.checkbox("🔬 Advanced Analytics", value=True)
            
        else:  # Legacy mode
            st.markdown("### ⚙️ Legacy Settings")
            
            project_filter = st.selectbox("Project Filter", ["All", "CEMEX", "RCC"])
            include_charts = st.checkbox("📊 Include Visualizations", value=True)
        
        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.info(f"""
        **Version:** 2.0 Enhanced
        **Mode:** {mode.split()[1]}
        **Status:** Online
        **User:** {user_role.title()}
        """)
    
    # Unified File Upload Section (feeds both modes)
    st.markdown("## 📁 Data Upload Center")
    st.markdown("*Upload files here - they will be available for both OPTIBAT Dashboard and Legacy Reports*")
    
    # Create unified upload area
    upload_col1, upload_col2, upload_col3 = st.columns(3)
    
    with upload_col1:
        st.markdown("#### 📄 OPTIBAT Files (.osf)")
        optibat_files = st.file_uploader(
            "Upload .osf files",
            type=['osf', 'txt', 'csv'],
            accept_multiple_files=True,
            key="unified_optibat_files"
        )
    
    with upload_col2:
        st.markdown("#### 📊 Statistics (.txt/.csv)")
        stats_files = st.file_uploader(
            "Upload statistics files",
            type=['txt', 'csv'],
            accept_multiple_files=True,
            key="unified_stats_files"
        )
    
    with upload_col3:
        st.markdown("#### 📈 Data Files (.xlsx/.csv)")
        data_files = st.file_uploader(
            "Upload data files",
            type=['xlsx', 'csv', 'xls'],
            accept_multiple_files=True,
            key="unified_data_files"
        )
    
    # Store uploaded files in session state for both modes
    if 'unified_files' not in st.session_state:
        st.session_state.unified_files = {}
    
    st.session_state.unified_files['optibat'] = optibat_files or []
    st.session_state.unified_files['stats'] = stats_files or []
    st.session_state.unified_files['data'] = data_files or []
    
    # Show upload status
    total_files = len(st.session_state.unified_files['optibat']) + len(st.session_state.unified_files['stats']) + len(st.session_state.unified_files['data'])
    if total_files > 0:
        st.success(f"✅ {total_files} files uploaded successfully - Available for both analysis modes!")
    
    st.markdown("---")
    
    # Main content based on selected mode
    if "OPTIBAT" in mode:
        show_optibat_dashboard(st.session_state.unified_files)
    else:
        show_legacy_reports(st.session_state.unified_files)
    
    # Enhanced footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: {OPTIMITIVE_COLORS['text_secondary']}; 
                padding: 2rem; background: {OPTIMITIVE_COLORS['medium_bg']}; 
                border-radius: 10px; margin-top: 2rem;">
        <h4 style="color: {OPTIMITIVE_COLORS['primary_red']};">OPTIMITIVE ANALYTICS SUITE</h4>
        <p><strong>© 2024 Optimitive | AI Optimization Solutions</strong></p>
        <p>🌐 <a href="https://optimitive.com" target="_blank" style="color: {OPTIMITIVE_COLORS['primary_red']};">optimitive.com</a></p>
        <p><strong>Developed by Juan Cruz E.</strong> | Enhanced v2.0 | Last Update: {datetime.now().strftime('%Y-%m-%d')}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()