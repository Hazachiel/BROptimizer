@echo off

:: ────────────────────────────────────────────────
setlocal
:: Configuración (ajusta estas líneas si cambias paths)
for /f "delims=" %%i in ('where nw.exe') do set "NW_PATH=%%i"
set "PROFILE_DIR=%localappdata%\RPGM\User Data"
set "GAME_DIR=%~dp0"
:: ────────────────────────────────────────────────

echo.
echo Preparando entorno RPG Maker (NW.js portable compartido)...

:: 1. Limpiar solo caches temporales, preservando partidas y datos del usuario
if exist "%PROFILE_DIR%" (
    echo Limpiando cache temporal...
    for %%D in ("%PROFILE_DIR%\Default\Cache" "%PROFILE_DIR%\Default\Code Cache" "%PROFILE_DIR%\Default\GPUCache" "%PROFILE_DIR%\ShaderCache") do rd /s /q "%%~D" 2>nul
) else (
    echo No existia perfil anterior, continuando...
)

:: 2. Lanzar el juego usando el mismo perfil limpio
if not exist "%NW_PATH%" (
    echo ERROR: No se encuentra nw.exe en Path
    echo    %NW_PATH%
    echo Instala/actualiza NW.js portable en esa ubicación.
    pause
    exit /b 1
)

echo Iniciando juego...
start "" "%NW_PATH%" --user-data-dir="%PROFILE_DIR%" --nwapp "%GAME_DIR%"

endlocal
exit /b 0