import chromadb
import openai
import time
import numpy as np

# Set your OpenAI API key
openai.api_key = "your-api-key-here"

# 1. Get embeddings using OpenAI API
def get_embedding(text):
    while True:
        try:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response['data'][0]['embedding']
        except openai.error.RateLimitError:
            print("Rate limit exceeded. Waiting for 20 seconds.")
            time.sleep(20)

# 2. Reorder documents
def reorder_documents(docs):
    n = len(docs)
    reordered = []
    for i in range(n):
        if i % 2 == 0:
            reordered.append(docs[i // 2])
        else:
            reordered.append(docs[-(i // 2 + 1)])
    return reordered

# 3. Query OpenAI
def query_openai(prompt):
    while True:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message['content']
        except openai.error.RateLimitError:
            print("Rate limit exceeded. Waiting for 20 seconds.")
            time.sleep(20)

# Main process
def main():
    texts = [
        "Basquetball is a great sport.",
        "Fly me to the moon is one of my favourite songs.",
        "The Celtics are my favourite team.",
        "This is a document about the Boston Celtics",
        "I simply love going to the movies",
        "The Boston Celtics won the game by 20 points",
        "This is just a random text.",
        "Elden Ring is one of the best games in the last 15 years.",
        "L. Kornet is one of the best Celtics players.",
        "Larry Bird was an iconic NBA player.",
    ]
    
    # Initialize ChromaDB client
    chroma_client = chromadb.Client()
    
    # Create or get a collection
    collection = chroma_client.create_collection(name="my_collection")
    
    # Add documents to the collection
    collection.add(
        documents=texts,
        ids=[f"id_{i}" for i in range(len(texts))],
        embeddings=[get_embedding(text) for text in texts]
    )
    
    # Query
    query = "What can you tell me about the Celtics?"
    query_embedding = get_embedding(query)
    
    # Retrieve documents
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10
    )
    
    # Reorder documents
    reordered_docs = reorder_documents(results['documents'][0])
    
    # Prepare context for OpenAI query
    context = "\n".join(reordered_docs)
    prompt = f"""Given this text extracts:
    -----
    {context}
    -----
    Please answer the following question:
    {query}"""
    
    # Query OpenAI
    response = query_openai(prompt)
    
    print(response)

if __name__ == "__main__":
    main()
