import pandas as pd
import os
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

def load_and_chunk_pdf(file_path: str) -> list[Document]:
    """
    Simple, dependency-free PDF loader using PyPDF.
    No model downloads required.
    """
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    chunks = splitter.split_documents(pages)

    filename = os.path.basename(file_path)
    for chunk in chunks:
        chunk.metadata["source"] = filename

    return chunks

def load_csv_as_semantic_docs(file_path: str) -> list[Document]:
    """
    Converts CSV rows into semantic documents for the vector store.
    """
    df = pd.read_csv(file_path)
    docs = []
    for index, row in df.iterrows():
        row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
        docs.append(Document(
            page_content=row_text,
            metadata={
                "source": os.path.basename(file_path),
                "row_index": index,
                "doc_type": "csv_record"
            }
        ))
    return docs