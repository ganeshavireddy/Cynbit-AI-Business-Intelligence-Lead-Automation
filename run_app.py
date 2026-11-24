"""
run_app.py - Unified Production Entrypoint
Launches both the FastAPI backend and Streamlit dashboard in parallel.
Optimized for Render, Railway, Docker, and Cloud PaaS deployments.
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

    # Ensure frontend knows where to call the local backend
    if "API_BASE_URL" not in os.environ:
        os.environ["API_BASE_URL"] = f"http://127.0.0.1:{backend_port}"

    print(f"[1/2] Launching FastAPI Backend on http://0.0.0.0:{backend_port}...")
    backend = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "backend.main:app",
            "--host", "0.0.0.0",
            "--port", str(backend_port)
        ],
        env=os.environ.copy()
    )

    # Allow FastAPI to warm up
    time.sleep(2)

    print(f"[2/2] Launching Streamlit Dashboard on http://0.0.0.0:{frontend_port}...")
    frontend = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "frontend/app.py",
            "--server.port", str(frontend_port),
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ],
        env=os.environ.copy()
    )

    print("\nCynbit AI Platform is live and operational!")
    print(f" - Streamlit UI: http://0.0.0.0:{frontend_port}")
    print(f" - FastAPI Docs: http://0.0.0.0:{backend_port}/docs\n")

    def shutdown(sig, frame):
        print("\nShutting down services...")
        try:
            backend.terminate()
        except Exception:
            pass
        try:
            frontend.terminate()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        frontend.wait()
    except KeyboardInterrupt:
        shutdown(None, None)

if __name__ == "__main__":
    main()
