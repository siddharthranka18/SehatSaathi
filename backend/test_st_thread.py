import threading

def load_st():
    print("loading sentence_transformers...")
    try:
        from sentence_transformers import SentenceTransformer
        print(f"sentence_transformers loaded! type={type(SentenceTransformer)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=load_st)
    t.start()
    t.join()
    print("done")
