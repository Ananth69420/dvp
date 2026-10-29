"""
LogLens AI - Application Runner
Runs the FastAPI server which serves both the API and the built React frontend.
"""

import os
import sys
import socket
import argparse
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

# Ensure backend directory is in sys.path and PYTHONPATH
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.environ["PYTHONPATH"] = str(BACKEND_DIR)


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether a TCP port is currently open and bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def find_available_port(start_port: int = 8000, host: str = "127.0.0.1", max_attempts: int = 10) -> int:
    """Finds start_port or the next available open port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p, host):
            return p
    return start_port


def prepare_environment():
    """Generates synthetic samples and builds frontend assets if not present."""
    # 1. Synthetic sample logs
    samples_dir = BACKEND_DIR / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    sample_files = list(samples_dir.glob("*.*"))
    if len(sample_files) < 5:
        print("[*] Generating synthetic sample logs...")
        try:
            import importlib
            sample_gen = importlib.import_module("app.services.sample_generator")
            sample_gen.generate_all_samples()
            print("[+] 5 synthetic sample logs generated successfully.")
        except Exception as e:
            print(f"[!] Warning generating sample logs: {e}")

    # 2. Frontend distribution build
    dist_dir = FRONTEND_DIR / "dist"
    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        print("[*] Frontend distribution not found. Building static production assets...")
        import subprocess
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        try:
            res = subprocess.run([npm_cmd, "run", "build"], cwd=str(FRONTEND_DIR), shell=True)
            if res.returncode == 0:
                print("[+] Frontend build completed successfully.")
            else:
                print("[!] Note: Frontend build exited with warning. Serving existing static files.")
        except Exception as e:
            print(f"[!] Warning building frontend: {e}")


def main():
    parser = argparse.ArgumentParser(description="LogLens AI Application Runner")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reloading")
    args = parser.parse_args()

    print("=" * 64)
    print("   LogLens AI - Log Parser & AI-Assisted Visualization System   ")
    print("=" * 64)

    # Prepare environment assets
    prepare_environment()

    # Determine port
    port = args.port
    if is_port_in_use(port, args.host):
        alt_port = find_available_port(start_port=port + 1, host=args.host)
        print(f"\n[!] Port {port} is currently occupied by another process.")
        print(f"[*] Automatically switching to available port: {alt_port}")
        port = alt_port

    # Switch working directory to backend so all relative imports & app modules resolve cleanly
    os.chdir(str(BACKEND_DIR))

    print(f"\n[+] Starting FastAPI Server on http://{args.host}:{port}")
    print(f"[+] Web Application UI: http://{args.host}:{port}")
    print(f"[+] API Documentation: http://{args.host}:{port}/docs")
    print("[+] Press Ctrl+C to stop the server at any time.\n")

    try:
        import uvicorn
        # Run uvicorn cleanly without reload subprocess issues on Windows
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=port,
            reload=not args.no_reload,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n\n[+] LogLens AI server stopped cleanly.")
    except Exception as e:
        print(f"\n[!] Server encountered an error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[+] LogLens AI server stopped cleanly.")
        sys.exit(0)
