@echo off
chcp 65001 >nul
cd /d "C:\Users\Administrator\CODE\snap-educational-mcp"
call venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
python -m mcp_server.main