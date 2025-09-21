# 🚀 Optimitive Analytics Suite - Version 2.0 Enhanced

## 📋 Upgrade Notes

### ✨ New Features Added

#### 1. **Real-time OPTIBAT Dashboard**
- 📊 Live monitoring of OPTIBAT system flags
- 💓 Heartbeat signal analysis with health status
- 📈 Interactive timeline visualizations
- 🎯 Advanced KPI calculations (uptime, communication health, data quality)
- 🔄 Auto-refresh capabilities

#### 2. **Enhanced Authentication System**
- 👥 Role-based access (admin, user, analyst)
- 🔐 Extended user management
- 📊 Session tracking and IP logging

#### 3. **Google Sheets Metrics Integration**
- 📈 Automatic access logging to Google Sheets
- 🌐 IP tracking and usage analytics
- ⏰ Timezone-aware logging (Madrid timezone)

#### 4. **Advanced Analytics Engine**
- 🧮 Sophisticated signal processing
- 🔍 Stuck signal detection
- 📊 Pulse rate calculations
- ⚠️ Automated alert generation

#### 5. **Dual-Mode Operation**
- 🔄 **OPTIBAT Mode**: Real-time dashboard with live data
- 📋 **Legacy Mode**: Traditional monthly reports
- 🎛️ Easy mode switching via sidebar

### 📁 File Structure

```
mtto streamlit/
├── monthly_report_app.py              # Original application
├── monthly_report_app_backup.py       # Backup of original
├── monthly_report_app_enhanced.py     # New enhanced version ⭐
├── requirements.txt                   # Updated dependencies
├── credenciales_login.txt            # Login credentials
├── UPGRADE_NOTES.md                  # This file
└── .streamlit/
    └── secrets.toml                  # Authentication config
```

### 🔑 Authentication

#### Default Users:
- **Administrador** (admin role)
  - Usuario: `Administrador`
  - Contraseña: `admin123`
- **demo** (user role)
  - Usuario: `demo` 
  - Contraseña: `demo123`
- **optibat** (analyst role) - NEW
  - Usuario: `optibat`
  - Contraseña: `optibat2024`

### 🌐 Access URLs

- **Original App**: http://localhost:8501
- **Enhanced App**: http://localhost:8502
- **Network Access**: http://192.168.1.131:8501 / :8502

### 🔧 Configuration

#### Required Secrets (Optional):
```toml
# .streamlit/secrets.toml

# Google Sheets Integration
[gcp_service_account]
# JSON credentials for Google Sheets API

# Enhanced Authentication
[auth.users.admin]
password = "admin123"
name = "Administrator"
role = "admin"

[auth.users.optibat]
password = "optibat2024" 
name = "OPTIBAT Analyst"
role = "analyst"
```

### 🚀 Running the Applications

#### Original Version:
```bash
streamlit run monthly_report_app.py
```

#### Enhanced Version:
```bash
streamlit run monthly_report_app_enhanced.py --server.port 8502
```

#### Install New Dependencies:
```bash
pip install -r requirements.txt
```

### 📊 Key Differences

| Feature | Original | Enhanced |
|---------|----------|----------|
| **Dashboard** | Static reports only | Real-time + Static |
| **Authentication** | 2 users | 3+ users with roles |
| **Analytics** | Basic flag analysis | Advanced signal processing |
| **Visualization** | Simple charts | Interactive gauges + timelines |
| **Monitoring** | None | Google Sheets logging |
| **Modes** | Single mode | Dual mode (OPTIBAT + Legacy) |

### ⚠️ Breaking Changes

1. **Port Change**: Enhanced version runs on port 8502 by default
2. **New Dependencies**: Requires `gspread`, `oauth2client`, `pytz`
3. **User Roles**: Added role-based access control
4. **Mode Selection**: UI now has mode selection in sidebar

### 🔍 Testing Instructions

1. **Start Enhanced Version**:
   ```bash
   cd "C:\Users\JuanCruz\Desktop_Local\mtto streamlit"
   streamlit run monthly_report_app_enhanced.py --server.port 8502
   ```

2. **Login with new user**:
   - Usuario: `optibat`
   - Contraseña: `optibat2024`

3. **Test OPTIBAT Dashboard**:
   - Select "🔄 OPTIBAT Real-time Dashboard"
   - Upload .txt/.osf files
   - Verify KPI gauges and timeline charts

4. **Test Legacy Reports**:
   - Select "📋 Legacy Monthly Reports" 
   - Upload files and generate reports
   - Verify compatibility with original functionality

### 📈 Performance Notes

- **Caching**: Enhanced file processing with `@st.cache_data`
- **Memory**: Improved data handling for large files
- **Responsiveness**: Better progress indicators and status messages
- **Error Handling**: More robust error catching and user feedback

### 🛠️ Troubleshooting

#### Common Issues:

1. **Google Sheets Access Denied**:
   - Solution: Ensure GCP service account is configured in secrets

2. **Port Already in Use**:
   - Solution: Use different port with `--server.port 8503`

3. **Missing Dependencies**:
   - Solution: Run `pip install -r requirements.txt`

4. **Authentication Failed**:
   - Solution: Check `.streamlit/secrets.toml` configuration

### 🔄 Migration Path

To migrate from original to enhanced:

1. **Backup Data**: Original app and settings backed up
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Update Secrets**: Add new user roles to secrets.toml
4. **Test Functionality**: Verify both modes work correctly
5. **Switch Default**: Replace original when ready

### 📞 Support

For issues or questions:
- Check error logs in Streamlit interface
- Verify all dependencies are installed
- Ensure proper authentication configuration
- Contact: Juan Cruz E. (Developer)

---

**Version**: 2.0 Enhanced  
**Release Date**: 2024-08-14  
**Compatibility**: Python 3.8+, Streamlit 1.37+