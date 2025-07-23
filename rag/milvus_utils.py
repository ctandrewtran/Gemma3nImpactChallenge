from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from typing import List, Dict, Optional
import time

MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
DEFAULT_COLLECTION_NAME = "rag_documents"

# Example index registry (can be persisted)
INDEX_REGISTRY = {
    "rag_documents": {"description": "General local government data", "domain": "general"},
    # Add more indexes as needed
    # "farming_data": {"description": "Farming and agriculture policies", "domain": "farming"},
}

# Define schema (all indexes use same schema for now)
def get_schema():
    return CollectionSchema([
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2048),
        FieldSchema(name="url", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="date", dtype=DataType.VARCHAR, max_length=32),
    ], description="RAG document collection")


def list_indexes() -> Dict[str, Dict]:
    """
    List all available indexes (collections) and their metadata.
    """
    return INDEX_REGISTRY.copy()


def connect_milvus(index_name: Optional[str] = None) -> Collection:
    """
    Connect to Milvus and return the collection object for the given index.
    Create collection if not exists. Defaults to DEFAULT_COLLECTION_NAME.
    """
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    name = index_name or DEFAULT_COLLECTION_NAME
    if name not in Collection.list_collections():
        col = Collection(name, get_schema())
        col.create_index("embedding", {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}})
        col.load()
    else:
        col = Collection(name)
        col.load()
    return col


def insert_embeddings(embeddings: List[List[float]], metadatas: List[Dict], index_name: Optional[str] = None):
    """
    Insert embeddings and metadata into the specified Milvus index.
    Each metadata dict should have 'text', 'url', and 'date'.
    """
    col = connect_milvus(index_name)
    data = [
        [None] * len(embeddings),  # id (auto)
        embeddings,
        [m["text"] for m in metadatas],
        [m["url"] for m in metadatas],
        [m["date"] for m in metadatas],
    ]
    try:
        col.insert(data)
        col.flush()
    except Exception as e:
        print(f"[Milvus] Insert error: {e}")


def search_embeddings(query_embedding: List[float], top_k: int = 5, index_name: Optional[str] = None) -> List[Dict]:
    """
    Search the specified Milvus index for similar embeddings. Returns list of dicts with text, url, and score.
    """
    col = connect_milvus(index_name)
    try:
        results = col.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["text", "url", "date"]
        )
        hits = results[0]
        return [
            {"text": hit.entity.get("text"), "url": hit.entity.get("url"), "date": hit.entity.get("date"), "score": hit.distance}
            for hit in hits
        ]
    except Exception as e:
        print(f"[Milvus] Search error: {e}")
        return []


def register_index(index_name: str, description: str, domain: str):
    """
    Register a new index (collection) in the registry.
    """
    INDEX_REGISTRY[index_name] = {"description": description, "domain": domain} 