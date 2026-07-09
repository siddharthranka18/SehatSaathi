import threading

def load_lib():
    print("loading transformers...")
    try:
        import transformers
        print("transformers loaded!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=load_lib)
    t.start()
    t.join()
    print("done")
