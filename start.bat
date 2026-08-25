@echo off
echo Starting Vera Merchant AI Bot...
echo.

echo [1/2] Starting Python Backend Server...
start "Vera Backend" cmd /k "python -m uvicorn bot:app --host 0.0.0.0 --port 8080"

echo [2/2] Starting React Frontend Server...
cd frontend
if not exist "node_modules\" (
    echo Installing frontend dependencies...
    npm install
)
start "Vera Frontend" cmd /c "npm run dev"

echo.
echo Both servers are starting up! 
echo A new window has been opened for the backend, and another for the frontend.
echo The frontend will be available at http://localhost:5173
echo.
pause
