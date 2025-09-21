# Optimitive Monthly Report Generator

A Streamlit application for generating monthly maintenance reports with integrated SharePoint file browsing and Microsoft Graph API support.

## Features

- 🔐 **Secure Authentication**: User authentication with session management
- 📁 **SharePoint Integration**: Browse and access SharePoint files directly
- 📊 **Report Generation**: Create comprehensive monthly maintenance reports
- 📈 **Data Visualization**: Interactive charts and statistics
- 🎨 **Professional UI**: Clean, responsive interface
- 📱 **Mobile Friendly**: Responsive design for all devices

## Prerequisites

- Python 3.8 or higher
- Microsoft Azure AD Application (for SharePoint access)
- Streamlit account (optional, for deployment)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mtto-streamlit
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Create Streamlit secrets file**
   ```bash
   mkdir .streamlit
   cp secrets_example.toml .streamlit/secrets.toml
   ```

2. **Configure authentication and SharePoint settings**
   
   Edit `.streamlit/secrets.toml`:
   
   ```toml
   [auth]
   cookie_name = "optimitive_monthly_report"
   cookie_key = "your-random-secret-key-at-least-32-chars-long"
   cookie_expiry_days = 30
   names = ["Admin User", "Your Name"]
   usernames = ["admin", "youruser"]
   passwords = ["$2b$12$...", "$2b$12$..."]  # Hashed passwords
   
   [graph]
   tenant_id = "your-azure-tenant-id"
   client_id = "your-azure-app-client-id"
   client_secret = "your-azure-app-client-secret"
   hostname = "yourcompany.sharepoint.com"
   site_path = "sites/YourSiteName"
   drive_name = "Documents"
   ```

3. **Generate password hashes**
   ```python
   import streamlit_authenticator as stauth
   hashed_passwords = stauth.Hasher(['your_password']).generate()
   print(hashed_passwords)
   ```

## Azure AD Setup

1. **Register an application** in Azure Portal
2. **Add API permissions**:
   - Sites.Read.All or Sites.ReadWrite.All
   - Files.Read.All or Files.ReadWrite.All
3. **Grant admin consent** for the permissions
4. **Generate a client secret**
5. **Configure redirect URIs** (if needed)

## Usage

1. **Start the application**
   ```bash
   streamlit run monthly_report_app.py
   ```

2. **Access the application**
   - Open your browser to `http://localhost:8501`
   - Login with your configured credentials

3. **Generate reports**
   - Browse SharePoint files
   - Select files for analysis
   - Configure report parameters
   - Generate and download reports

## Project Structure

```
mtto-streamlit/
├── monthly_report_app.py      # Main application file
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore patterns
├── README.md                 # This file
├── secrets_example.toml      # Configuration template
└── .streamlit/
    └── secrets.toml          # Configuration (not in git)
```

## Security Notes

- Never commit `secrets.toml` to version control
- Use strong, unique passwords
- Regularly rotate client secrets
- Use environment variables in production
- Enable MFA for Azure AD accounts

## Deployment

### Streamlit Cloud

1. Connect your GitHub repository
2. Configure secrets in Streamlit Cloud dashboard
3. Deploy automatically from main branch

### Local Production

1. Use a production WSGI server
2. Configure environment variables
3. Set up SSL certificates
4. Configure firewall rules

## Development

1. **Code formatting**
   ```bash
   black monthly_report_app.py
   ```

2. **Run tests** (if applicable)
   ```bash
   python -m pytest
   ```

## Troubleshooting

### Common Issues

1. **Authentication errors**
   - Verify Azure AD configuration
   - Check client secret expiration
   - Ensure proper API permissions

2. **SharePoint access issues**
   - Verify site URL and paths
   - Check user permissions
   - Validate tenant configuration

3. **Import errors**
   - Ensure all dependencies are installed
   - Check Python version compatibility
   - Verify virtual environment activation

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Azure AD configuration
3. Verify SharePoint permissions
4. Check application logs

## License

This project is proprietary software. All rights reserved.

## Contributing

Please follow the established coding standards and submit pull requests for review.