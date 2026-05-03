import subprocess
import time
import os
import sys

print("Cleaning up old server processes to free port 8080...")
subprocess.run('FOR /F "tokens=5" %T IN (\'netstat -a -n -o ^| find "8080"\') DO TaskKill.exe /F /PID %T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("==================================================")
print("1. Starting Backend Server (bot.py) in the background...")
print("==================================================")

# Determine the correct python executable
python_exe = sys.executable
if os.path.exists(r"d:\MULTIBOTS\venv\Scripts\python.exe"):
    python_exe = r"d:\MULTIBOTS\venv\Scripts\python.exe"

# Start the uvicorn server as a background process
server_process = subprocess.Popen(
    [python_exe, "-m", "uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "8080"],
    cwd=r"d:\MULTIBOTS"
)

print("Waiting 5 seconds for the server to fully start up...")
time.sleep(5)

# Check if server crashed immediately
if server_process.poll() is not None:
    print("\n[ERROR] The backend server crashed on startup!")
    sys.exit(1)

print("\n==================================================")
print("2. Running the Judge Simulator...")
print("==================================================")

judge_process = subprocess.Popen(
    [python_exe, "judge_simulator.py"],
    cwd=r"d:\MULTIBOTS\magicpin-ai-challenge",
)
judge_process.wait()

print("\n==================================================")
print("3. Shutting down the backend server...")
print("==================================================")
server_process.terminate()
print("Done!")
