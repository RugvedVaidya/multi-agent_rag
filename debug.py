# paste this into a new file called debug.py
import chromadb
import config

db  = chromadb.PersistentClient(path=config.CHROMA_DIR)
col = db.get_or_create_collection(config.COLLECTION_NAME)

results = col.get(limit=10, include=["documents", "metadatas"])
for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
    print(f"\n--- Chunk {i} | {meta['file_name']} ---")
    print(doc[:300])