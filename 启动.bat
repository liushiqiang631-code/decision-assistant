@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Decision Assistant

rem If already running, just open the web page
netstat -ano | findstr ":8735" | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
  start "" http://localhost:8735
  exit
)

rem Find a windowless pythonw: prefer "where pythonw",
rem otherwise derive pythonw.exe from each python.exe path
set "PYW="
for /f "delims=" %%i in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%i"
if not defined PYW (
  for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PYW if /i "%%~xi"==".exe" (
      set "cand=%%~dpniw.exe"
      if exist "!cand!" if /i not "!cand!"=="C:\Windows\System32\pythonw.exe" set "PYW=!cand!"
    )
  )
)

if defined PYW (
  start "" "!PYW!" server.py
) else (
  rem Fallback: minimized visible window
  start /min cmd /c "python server.py"
)
exit
