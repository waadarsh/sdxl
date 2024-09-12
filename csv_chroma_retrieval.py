# retrieval_script.py

import chromadb
from chromadb.config import Settings
from chromadb_mistral_embeddings import MistralEmbeddingFunction
from dotenv import load_dotenv
from mistralai.client import MistralClient
import pandas as pd
import ast
import logging
import colorlog
import sys

# Set up logger
def setup_logger():
    logger = colorlog.getLogger()
    logger.setLevel(logging.INFO)
    handler = colorlog.StreamHandler(stream=sys.stderr)
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    logger.addHandler(handler)
    return logger

logger = setup_logger()

# Load environment variables
load_dotenv('.env')
client = MistralClient()

# Initialize Chroma client
chroma_client = chromadb.PersistentClient(path="./chromadb_csv", settings=Settings(anonymized_telemetry=False))

def get_collection(collection_name):
    """Get or create a collection."""
    return chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=MistralEmbeddingFunction(api_key=client._api_key, model_name="mistral-embed")
    )

def query_collection(collection, query_text, n_results=5):
    """Query the collection and return results."""
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["metadatas", "distances"]
    )
    return results

def process_query_results(results):
    """Process query results and return as a DataFrame."""
    rows = []
    for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
        row = {k: ast.literal_eval(v) if isinstance(v, str) and v.startswith('[') and v.endswith(']') else v 
               for k, v in metadata.items() if k not in ['filename', 'row_number', 'chunk_number']}
        row['distance'] = distance
        row['filename'] = metadata['filename']
        row['row_number'] = metadata['row_number']
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df = df.sort_values('row_number').drop_duplicates(subset='row_number', keep='first')
    return df

def main():
    logger.info("Starting retrieval process...")
    
    collection_name = input("Enter the name of the Chroma DB collection to query: ")
    collection = get_collection(collection_name)
    
    while True:
        query = input("Enter your query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        
        n_results = int(input("Enter the number of results to retrieve: "))
        
        results = query_collection(collection, query, n_results)
        df = process_query_results(results)
        
        print("\nQuery Results:")
        print(df)
        
        save_option = input("Do you want to save these results to a CSV file? (yes/no): ")
        if save_option.lower() == 'yes':
            filename = input("Enter the filename to save (e.g., results.csv): ")
            df.to_csv(filename, index=False)
            logger.info(f"Results saved to {filename}")
    
    logger.info("Retrieval process completed.")

if __name__ == "__main__":
    main()
