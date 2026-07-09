"""
Windows-safe uvicorn launcher.

Use this instead of `uvicorn app.main:app` when running locally on Windows.
The `if __name__ == '__main__':` guard is CRITICAL: when torch imports its C
extensions, it spawns child processes on Windows (multiprocessing spawn method).
Without this guard, each child re-imports this module and tries to start another
uvicorn on port 8000, which fails with exit code 1 and kills the parent too.

Usage:
    python run.py
    python run.py --host 0.0.0.0 --port 8000 --reload
"""

import multiprocessing
import os
import sys


if __name__ == "__main__":
    # Required for Windows: prevents spawned child processes from re-running server
    multiprocessing.freeze_support()

    # Prevent torch / OpenMP / MKL from spawning extra threads/processes at init time
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import uvicorn

    # Parse optional CLI overrides (--host, --port, --reload)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
