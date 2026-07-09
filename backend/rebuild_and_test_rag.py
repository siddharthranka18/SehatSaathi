import os
import sys
import json
import traceback
from pathlib import Path

# Ensure backend package is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Use in-memory Qdrant and BM25-only retrieval to avoid heavy models
os.environ['QDRANT_HOST'] = 'local'
os.environ['FAST_DEV'] = '1'

try:
    from app.services import rag_service

    INDEX_DIR = rag_service.INDEX_DIR
    GUIDELINES_DIR = rag_service.GUIDELINES_DIR

    store_path = INDEX_DIR / 'store.json'

    if not store_path.exists():
        print('store.json not found. Building minimal store from guidelines...')
        all_chunks = []
        parent_docs = {}
        for file in GUIDELINES_DIR.glob('*.txt'):
            with open(file, encoding='utf-8') as f:
                text = f.read()
            new_chunks = rag_service.create_parent_child_chunks(text, file.name)
            all_chunks.extend(new_chunks)
        data = {'chunks': all_chunks, 'parents': rag_service.parent_docs, 'vectors': []}
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with open(store_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print('Created store.json with', len(all_chunks), 'chunks')
    else:
        print('Loading existing store.json and merging new guideline files if present')
        with open(store_path, encoding='utf-8') as f:
            data = json.load(f)

        existing_sources = set(d.get('source') for d in data.get('chunks', []))

        added = 0
        for file in GUIDELINES_DIR.glob('*.txt'):
            src = file.name
            if src in existing_sources:
                continue
            with open(file, encoding='utf-8') as f:
                text = f.read()
            new_chunks = rag_service.create_parent_child_chunks(text, src)
            data['chunks'].extend(new_chunks)
            # rag_service.create_parent_child_chunks populates rag_service.parent_docs
            added += len(new_chunks)
        if added:
            # Merge parent docs
            data_parents = data.get('parents', {})
            data_parents.update(rag_service.parent_docs)
            data['parents'] = data_parents
            # No vectors for new chunks; leave 'vectors' as-is (may be empty)
            with open(store_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            print('Appended', added, 'new chunks and updated store.json')
        else:
            print('No new guideline files to merge')

    # Load updated store metadata into rag_service (builds BM25)
    with open(store_path, encoding='utf-8') as f:
        data = json.load(f)

    rag_service._load_store_metadata(data)
    print('Loaded store metadata into memory. Total chunks:', len(rag_service.chunks))

    queries = [
        'continuous stomachache',
        'abdominal pain',
        'gastritis',
        'food poisoning',
        'vomiting',
        'nausea',
        'constipation',
        'acidity'
    ]

    for q in queries:
        print('\nQUERY:', q)
        try:
            res = rag_service.retrieve_context(q, top_k=3)
            print('top_score:', res.get('top_score'))
            print('confident:', res.get('confident'))
            print('retrieved_sources:', res.get('retrieved_sources'))
            print('chunks:')
            for c in res.get('chunks', []):
                print(' -', c[:200])
        except Exception as e:
            print('Error retrieving for query:', q)
            traceback.print_exc()

except Exception as e:
    print('Fatal error in rebuild/test script')
    traceback.print_exc()
