import multiprocessing
import os

if __name__ == "__main__":
    multiprocessing.freeze_support()
    print("Main thread: importing sentence_transformers...")
    from sentence_transformers import SentenceTransformer
    print("Main thread: success")
