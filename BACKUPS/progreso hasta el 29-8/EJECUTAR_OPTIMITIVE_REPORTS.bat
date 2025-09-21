@echo off
echo ========================================
echo  OPTIMITIVE - MONTHLY REPORTS GENERATOR
echo  Desarrollado por Juan Cruz E.
echo ========================================
echo.
echo Iniciando aplicacion Streamlit...
echo.
echo URL de acceso: http://localhost:8081
echo Tambien disponible en: http://127.0.0.1:8081
echo.
echo Credenciales de acceso:
echo - Usuario: Administrador  / Password: admin123
echo - Usuario: demo          / Password: demo123  
echo.
echo Presiona Ctrl+C para detener la aplicacion
echo ========================================
echo.

cd /d "%~dp0"
streamlit run monthly_report_app.py --server.port=8081 --server.address=localhost

echo.
echo ========================================
echo Aplicacion cerrada. Presiona cualquier tecla para salir...
pause