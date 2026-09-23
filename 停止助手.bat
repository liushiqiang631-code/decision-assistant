@echo off
rem Stop the Decision Assistant background server (kills only the PID bound to port 8735)
set "FOUND="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8735" ^| findstr "LISTENING"') do (
  set "FOUND=1"
  taskkill /F /PID %%p >nul 2>nul
)
if defined FOUND (
  echo Decision Assistant stopped.
) else (
  echo Decision Assistant is not running.
)
timeout /t 2 >nul
