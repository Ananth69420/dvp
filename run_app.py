"""
LogLens AI - Application Runner
Runs the FastAPI server which serves both the API and the built React frontend on port 8000.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

def main():
    print("=" * 60)
    print(" LogLens AI - Log Parser & AI-Assisted Visualization System ")
    print("=" * 60)

    # Set PYTHONPATH
    os.environ["PYTHONPATH"] = str(BACKEND_DIR)

    # Check python environment
    venv_python = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    # Check if samples generated
    samples_dir = BACKEND_DIR / "samples"
    if not samples_dir.exists() or len(list(samples_dir.iterdir())) == 0:
        print("[*] Generating synthetic sample logs...")
        subprocess.run([python_cmd, "-m", "app.services.sample_generator"], cwd=str(BACKEND_DIR))

    # Check if frontend built
    dist_dir = FRONTEND_DIR / "dist"
    if not dist_dir.exists():
        print("[*] Building frontend assets...")
        subprocess.run(["npm.cmd", "run", "build"], cwd=str(FRONTEND_DIR), shell=True)

    print("\n[*] Starting FastAPI Backend & UI Server on http://127.0.0.1:8000 ...")
    print("[*] Press Ctrl+C to terminate.")
    subprocess.run([
        python_cmd, "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ], cwd=str(BACKEND_DIR))

if __name__ == "__main__":
    main()

