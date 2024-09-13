import fitz  # PyMuPDF
import openai
import chromadb
import os
import re
from typing import List, Callable, Dict, Any
from tqdm import tqdm
import colorlog
import logging

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up colorlog
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class RecursiveTextSplitter:
    def __init__(
        self,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
        length_function: Callable[[str], int] = len,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
        self.length_function = length_function

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            if _s == "":
                separator = _s
                break
            if re.search(re.escape(_s), text):
                separator = _s
                new_separators = separators[i + 1:]
                break

        # Now split the text
        splits = self._split_text_with_separator(text, separator)

        # Now go merging things, recursively splitting longer texts.
        _good_splits = []
        for s in splits:
            if self.length_function(s) < self.chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge_splits(_good_splits, separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge_splits(_good_splits, separator)
            final_chunks.extend(merged_text)
        return final_chunks

    def _split_text_with_separator(self, text: str, separator: str) -> List[str]:
        # Now that we have the separator, split the text
        if separator:
            splits = re.split(f"({re.escape(separator)})", text)
            splits = [s for s in splits if s != ""]
            return splits
        return list(text)

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        # We now want to combine these smaller pieces into medium size
        # chunks to send to the LLM.
        separator_len = self.length_function(separator)

        docs = []
        current_doc: List[str] = []
        total = 0
        for d in splits:
            _len = self.length_function(d)
            if total + _len + (separator_len if current_doc else 0) > self.chunk_size:
                if total > self.chunk_size:
                    logger.warning(f"Created a chunk of size {total}, which is longer than the specified {self.chunk_size}")
                if current_doc:
                    doc = separator.join(current_doc)
                    if doc:
                        docs.append(doc)
                    # Keep on popping if:
                    # - we have a larger chunk than in the chunk overlap
                    # - or if we still have any chunks and the length is long
                    while total > self.chunk_overlap or (
                        total + _len + (separator_len if current_doc else 0) > self.chunk_size and total > 0
                    ):
                        total -= self.length_function(current_doc[0]) + (separator_len if len(current_doc) > 1 else 0)
                        current_doc = current_doc[1:]
            current_doc.append(d)
            total += _len + (separator_len if len(current_doc) > 1 else 0)
        doc = separator.join(current_doc)
        if doc:
            docs.append(doc)
        return docs

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_semantic_info(chunk: str) -> str:
    prompt = f"""Extract key semantic information from the following text. Include main topics, key entities, and a brief summary:

{chunk}

Semantic Information:"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts key semantic information from text."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        n=1,
        temperature=0.5,
    )

    return response.choices[0].message.content.strip()

def generate_embedding(text: str) -> List[float]:
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

def store_in_chroma(collection: Any, text: str, semantic_info: str, embedding: List[float]):
    collection.add(
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"semantic_info": semantic_info}]
    )

def process_and_store_pdf(pdf_path: str, collection: Any, chunk_size: int = 1000, chunk_overlap: int = 200):
    # Extract text from PDF
    logger.info(f"Extracting text from {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    
    # Split text into chunks
    logger.info("Splitting text into chunks")
    splitter = RecursiveTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)
    
    # Process each chunk
    for chunk in tqdm(chunks, desc=f"Processing {os.path.basename(pdf_path)}", unit="chunk"):
        semantic_info = extract_semantic_info(chunk)
        embedding = generate_embedding(chunk)
        store_in_chroma(collection, chunk, semantic_info, embedding)

    logger.info(f"Processed and stored {len(chunks)} chunks from {pdf_path}")

def process_pdf_folder(folder_path: str, collection_name: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    # Initialize Chroma client and collection
    logger.info(f"Initializing Chroma collection: {collection_name}")
    client = chromadb.Client()
    collection = client.create_collection(collection_name)

    # Get all PDF files in the folder
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {folder_path}")
        return

    logger.info(f"Found {len(pdf_files)} PDF files in {folder_path}")

    # Process each PDF file
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs", unit="file"):
        pdf_path = os.path.join(folder_path, pdf_file)
        try:
            process_and_store_pdf(pdf_path, collection, chunk_size, chunk_overlap)
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}")

    logger.info(f"Finished processing all PDFs in {folder_path}")

# Example usage
if __name__ == "__main__":
    pdf_folder = "path/to/your/pdf/folder"
    collection_name = "multi_pdf_semantics_collection"
    chunk_size = 1000  # Adjust as needed
    chunk_overlap = 200  # Adjust as needed
    
    process_pdf_folder(pdf_folder, collection_name, chunk_size, chunk_overlap)
