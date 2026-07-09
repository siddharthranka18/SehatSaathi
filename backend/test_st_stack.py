import threading

def load_st():
    print("loading sentence_transformers...")
    try:
        from sentence_transformers import SentenceTransformer
        print(f"sentence_transformers loaded! type={type(SentenceTransformer)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Increase stack size to 8MB (default is typically 1MB on Windows)
    # The scipy/torch C extensions have deep call stacks during init
    threading.stack_size(8 * 1024 * 1024)
    
    t = threading.Thread(target=load_st)
    t.start()
    t.join()
    print("done")
