import threading

def load_torch():
    print("loading torch...")
    try:
        import torch
        print("torch loaded!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=load_torch)
    t.start()
    t.join()
    print("done")
