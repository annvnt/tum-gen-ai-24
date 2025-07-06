import os
import json
from camel.storages import ChromaStorage, VectorDBQuery, VectorRecord
from camel.types import VectorDistance
from jina_embeddings import JinaEmbedding  # <-- CHANGED: Import JinaEmbedding

# --- CONFIGURATION ---

# 1. Define the path to your JSON file
JSON_PATH = "my_data.json"

# 2. Define the Jina embedding model we'll use.
# This is a powerful and popular general-purpose model from Jina.
JINA_MODEL_NAME = "jina-embeddings-v3"

# 3. The vector dimension MUST match the model's output.
# Jina's v2 base model produces 768-dimensional vectors.
VECTOR_DIMENSION = 768  # <-- CHANGED: Dimension is now 768

# 4. Use a persistent client to save the processed data
STORAGE_PATH = "./camel_jina_storage"  # Using a new folder for the Jina DB
COLLECTION_NAME = "jina_json_collection"


# --- HELPER FUNCTION (No changes here) ---


def load_records_from_json(json_path: str) -> list:
    """Loads a list of records from a JSON file."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"The file {json_path} was not found.")
    print(f"Reading records from {json_path}...")
    with open(json_path, "r") as f:
        data = json.load(f)
    print(f"Successfully loaded {len(data)} records.")
    return data


# --- MAIN LOGIC ---


def main():
    """
    Main function to process the JSON, store it in Chroma, and run a query.
    """
    # 1. Initialize the Jina embedding model
    # The library will automatically pick up your JINA_API_KEY from the environment.
    print(f"Initializing Jina embedding model: {JINA_MODEL_NAME}")
    try:
        embedding_model = JinaEmbedding(model_name=JINA_MODEL_NAME)
    except Exception as e:
        print(
            f"Error initializing JinaEmbedding: {e}\n"
            "Please ensure your JINA_API_KEY environment variable is set correctly."
        )
        return

    # 2. Initialize ChromaStorage
    chroma_storage = ChromaStorage(
        vector_dim=VECTOR_DIMENSION,
        collection_name=COLLECTION_NAME,
        client_type="persistent",
        client_path=STORAGE_PATH,
        distance=VectorDistance.COSINE,
    )

    print(f"Clearing old data from collection '{COLLECTION_NAME}'...")
    chroma_storage.clear()

    # 3. Load records from JSON (No change)
    json_records = load_records_from_json(JSON_PATH)

    # 4. Prepare texts and VectorRecords (No change in logic)
    vector_records = []
    texts_to_embed = []
    for record in json_records:
        text_to_embed = f"Title: {record['title']}\nContent: {record['content']}"
        texts_to_embed.append(text_to_embed)
        vector_records.append(VectorRecord(payload=record))

    # 5. Generate embeddings using Jina's API
    print("Generating embeddings with Jina (this may take a moment)...")
    # The method is called .embed() instead of .encode()
    response = embedding_model.embed(texts=texts_to_embed)  # <-- CHANGED
    vector_embeddings = response["data"]

    # 6. Add vectors to their records
    for record, embedding_data in zip(vector_records, vector_embeddings):
        record.vector = embedding_data["embedding"]

    # 7. Add records to ChromaStorage (No change)
    print("Adding vector records to ChromaStorage...")
    chroma_storage.add(vector_records)
    print("✅ JSON data processed and stored successfully with Jina embeddings!")

    # 8. Query the stored vectors
    print("\n--- Running a test query ---")
    user_query = "What are the challenges for green energy?"
    # Use the same embedding model for the query
    query_response = embedding_model.embed(texts=[user_query])
    query_vector = query_response["data"][0]["embedding"]

    query_results = chroma_storage.query(
        VectorDBQuery(query_vector=query_vector, top_k=1)
    )

    print(f"\nQuery: '{user_query}'")
    print("Top result found in the JSON data:")
    for result in query_results:
        print(f"\nSimilarity Score: {result.similarity:.4f}")
        print("Retrieved Record (Payload):")
        print(json.dumps(result.record.payload, indent=2))


if __name__ == "__main__":
    if not os.path.exists(JSON_PATH):
        print(f"'{JSON_PATH}' not found. Please create it and run again.")
    else:
        main()