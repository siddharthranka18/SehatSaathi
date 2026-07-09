"""
Minimal test: does importing sentence_transformers in a background thread
crash the Python process on this Windows machine?

Run: python test_thread_import.py
"""

import threading
import time
import multiprocessing

multiprocessing.freeze_support()                  # Windows guard

import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def load():
    print("[thread] starting import...")
    try:
        t0 = time.perf_counter()
        from sentence_transformers import SentenceTransformer
        print(f"[thread] import done ({time.perf_counter()-t0:.2f}s)")

        t0 = time.perf_counter()
        model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        print(f"[thread] model loaded ({time.perf_counter()-t0:.2f}s)")
    except BaseException as e:
        import traceback
        print(f"[thread] FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    t = threading.Thread(target=load)
    t.start()
    print("[main] thread started, waiting 60s...")
    for i in range(60):
        if not t.is_alive():
            break
        time.sleep(1)
        print(f"[main] {i+1}s elapsed, thread alive={t.is_alive()}")
    t.join(timeout=5)
    print("[main] done")
