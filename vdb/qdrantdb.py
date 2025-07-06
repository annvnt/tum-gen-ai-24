import os
import json
from camel.storages import ChromaStorage, VectorDBQuery, VectorRecord
from camel.embeddings import JinaEmbedding
from camel.types import VectorDistance, EmbeddingModelType
from dotenv import load_dotenv # Recommended for API keys

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---

# 1. Define the path to your JSON data file
JSON_PATH = "mydata.json"

# 2. Configure the Jina Embedding Model
JINA_MODEL_TYPE = EmbeddingModelType.JINA_EMBEDDINGS_V3

# 3. CRITICAL: Set the vector dimension to match the Jina model's output.
VECTOR_DIMENSION = 1024

# 4. Configure the ChromaDB Storage
STORAGE_PATH = "./jina_v3_chroma_db"
COLLECTION_NAME = "documents_with_jina_v3"


def main():
    """
    Main function to demonstrate the combined workflow:
    1. Load JSON data.
    2. Generate embeddings with Jina v3.
    3. Store vectors and payloads in ChromaDB.
    4. Perform a semantic query.
    """
    print("--- Step 1: Initializing Clients ---")

    # Initialize the Jina embedding model
    try:
        jina_embed = JinaEmbedding(model_type=JINA_MODEL_TYPE)
        print(f"JinaEmbedding client initialized for model: {JINA_MODEL_TYPE.value}")
    except Exception as e:
        print(
            f"Error initializing JinaEmbedding: {e}\n"
            "Please ensure your JINA_API_KEY environment variable is set."
        )
        return

    # Initialize the ChromaStorage client
    chroma_storage = ChromaStorage(
        vector_dim=VECTOR_DIMENSION,
        collection_name=COLLECTION_NAME,
        client_type="persistent",
        path=STORAGE_PATH,
        distance=VectorDistance.COSINE,
    )
    print(f"ChromaStorage initialized at: {STORAGE_PATH}")
    print(f"Vector dimension set to: {chroma_storage.status().vector_dim}")

    # Clear old data for a clean run
    print("\n--- Step 2: Preparing Data ---")
    chroma_storage.clear()
    print(f"Cleared old data from collection '{COLLECTION_NAME}'.")

    # Load the records from the JSON file
    with open(JSON_PATH, "r") as f:
        json_records = json.load(f)
    print(f"Loaded {len(json_records)} records from '{JSON_PATH}'.")

    # Prepare a list of texts to be embedded
    texts_to_embed = [
        f"Title: {record['title']}\nContent: {record['content']}"
        for record in json_records
    ]

    print("\n--- Step 3: Generating Embeddings with Jina v3 ---")
    # Generate all embeddings in a single API call for efficiency
    # FIX: Changed keyword argument from 'texts' to 'objs'
    vector_embeddings = jina_embed.embed_list(objs=texts_to_embed)
    print(f"Successfully generated {len(vector_embeddings)} embeddings.")

    print("\n--- Step 4: Storing Records in ChromaDB ---")
    # Create VectorRecord objects, combining the vector with the original data
    vector_records_to_add = [
        VectorRecord(vector=emb, payload=original_record)
        for emb, original_record in zip(vector_embeddings, json_records)
    ]

    # Add the complete records to ChromaStorage
    chroma_storage.add(vector_records_to_add)
    status = chroma_storage.status()
    print(f"Successfully added records. New vector count: {status.vector_count}")

    print("\n--- Step 5: Performing a Semantic Query ---")
    user_query = "What are the safety improvements in energy storage?"

    # IMPORTANT: Embed the query using the SAME Jina model
    query_vector = jina_embed.embed(obj=user_query)

    # Query ChromaDB to find the most relevant documents
    query_results = chroma_storage.query(
        VectorDBQuery(query_vector=query_vector, top_k=1)
    )

    print(f"\nQuery: '{user_query}'")
    print("Top result from ChromaDB:")
    for result in query_results:
        print(f"\nSimilarity Score (Cosine): {result.similarity:.4f}")
        print("Retrieved Document Payload:")
        print(json.dumps(result.record.payload, indent=2))


if __name__ == "__main__":
    main()