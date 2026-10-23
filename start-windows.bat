@echo off
rem Abre o Claude Usage Tray na bandeja (sem janela de console). Instala na primeira vez.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo Primeira execução: rodando o instalador ...
    call "%~dp0install-windows.bat"
    exit /b
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0main.pyw"
