"""
run_app.py - Unified Production Entrypoint
Launches both the FastAPI backend and Streamlit dashboard in parallel.
"""

import subprocess
import sys
import time
import os
import signal

def main():
    print("=" * 65)
    print("Starting Cynbit AI Business Intelligence & Lead Automation Agent")
    print("=" * 65)

    backend_port = os.getenv("PORT_BACKEND", "8000")
    frontend_port = os.getenv("PORT", os.getenv("PORT_FRONTEND", "8501"))

    print(f"[1/2] Launching FastAPI Backend on http://0.0.0.0:{backend_port}...")
    backend = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0",
        "--port", str(backend_port)
    ])

    # Allow FastAPI to warm up
    time.sleep(2)

    print(f"[2/2] Launching Streamlit Dashboard on http://0.0.0.0:{frontend_port}...")
    frontend = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", str(frontend_port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ])

    print("\nCynbit AI Platform is live and operational!")
    print(f" - Streamlit UI: http://localhost:{frontend_port}")
    print(f" - FastAPI Docs: http://localhost:{backend_port}/docs\n")

    def shutdown(sig, frame):
        print("\nShutting down services...")
        backend.terminate()
        frontend.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        frontend.wait()
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    main()
