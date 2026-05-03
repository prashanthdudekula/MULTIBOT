@echo off
echo Cleaning up old server processes...

FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| find "8080"') DO (
  echo Killing backend process %%T
  TaskKill.exe /F /PID %%T
)

FOR /F "tokens=5" %%T IN ('netstat -a -n -o ^| find "5173"') DO (
  echo Killing frontend process %%T
  TaskKill.exe /F /PID %%T
)

echo Done! Now try running start.bat again.
pause
