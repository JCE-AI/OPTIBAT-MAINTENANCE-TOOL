@echo off
echo ========================================
echo    OPTIBAT MAINTENANCE TOOL - DASH
echo    Optimitive Monthly Report Generator
echo ========================================
echo.
echo Instalando dependencias...
pip install -r requirements.txt
echo.
echo Iniciando aplicacion Dash...
echo URL: http://127.0.0.1:8082
echo.
python monthly_report_dash_app.py
echo.
echo Presiona cualquier tecla para continuar...
pause >nul