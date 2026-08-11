@echo off
title RestaurantOS - Multi-Agent Launcher
echo ============================================================
echo   🍽️  RestaurantOS — Multi-Agent System Launcher
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/2] Starting FastAPI Backend (Port 8000)...
start "RestaurantOS Backend" cmd /k "python -m uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Streamlit Dashboard (Port 8501)...
start "RestaurantOS Dashboard" cmd /k "python -m streamlit run streamlit_app.py --server.port 8501"

echo.
echo ============================================================
echo   ✅ App Launched Successfully!
echo   📍 Dashboard: http://localhost:8501
echo   📍 API Docs:  http://localhost:8000/docs
echo ============================================================
echo.
pause
