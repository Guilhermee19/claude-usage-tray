@echo off
rem Instala o Claude Usage Tray no Windows: ambiente virtual, dependências, atalho no Menu Iniciar
rem e (opcional) início automático. Uso: install-windows.bat [--uninstall]
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Claude Usage Tray - Instalador

if /i "%~1"=="--uninstall" goto :uninstall

echo.
echo   Claude Usage Tray - instalação no Windows
echo   ==========================================
echo.

set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1 && set "PY=python"
if not defined PY (
    echo [ERRO] Python 3.10 ou mais novo não encontrado.
    echo        Instale com:  winget install Python.Python.3.12
    echo        ou baixe em:  https://www.python.org/downloads/  ^(marque "Add python.exe to PATH"^)
    goto :fail
)

echo [1/4] Criando ambiente virtual em .venv ...
if not exist ".venv\Scripts\python.exe" (
    %PY% -m venv .venv || goto :fail
)

echo [2/4] Instalando dependências ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q --upgrade pip || goto :fail
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || goto :fail

echo [3/4] Criando atalhos ...
set "AUTOSTART="
choice /c SN /n /m "      Iniciar junto com o Windows? [S/N] "
if errorlevel 2 (set "AUTOSTART=") else (set "AUTOSTART=--autostart")
".venv\Scripts\python.exe" -m claude_usage_tray.setup_cli --install %AUTOSTART% || goto :fail

echo [4/4] Abrindo o Claude Usage ...
call "%~dp0start-windows.bat"

echo.
echo   Pronto! O ícone está na bandeja, perto do relógio.
echo   Se não aparecer, clique na seta ^ e arraste o ícone para a barra.
echo.
pause
exit /b 0

:uninstall
echo Removendo atalhos e ambiente virtual ...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*%~dp0main.pyw*' } | Invoke-CimMethod -MethodName Terminate" >nul 2>&1
if exist ".venv\Scripts\python.exe" ".venv\Scripts\python.exe" -m claude_usage_tray.setup_cli --uninstall
if exist ".venv" rmdir /s /q ".venv"
echo Pronto. Suas configurações ficam em %%APPDATA%%\ClaudeUsageTray (pode apagar se quiser).
pause
exit /b 0

:fail
echo.
echo [ERRO] A instalação não terminou. Veja a mensagem acima.
pause
exit /b 1
