import os

from google import genai
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ..config import GEMINI_API_KEY, VECTOR_DB_PATH

# Gemini Developer API model id for `client.models.embed_content`
_DEFAULT_GEMINI_EMBED_MODEL = "gemini-embedding-2"


class _GeminiGenaiEmbeddings(Embeddings):
    """LangChain `Embeddings` backed by Google's `google-genai` SDK."""

    def __init__(self, api_key: str, model: str = _DEFAULT_GEMINI_EMBED_MODEL) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        self._model = model
        self._client = genai.Client(api_key=api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        for text in texts:
            resp = self._client.models.embed_content(
                model=self._model,
                contents=text
            )
            if not resp.embeddings or resp.embeddings[0].values is None:
                raise RuntimeError("Gemini embedding missing values")
            out.append(list(resp.embeddings[0].values))
        return out

    def embed_query(self, text: str) -> list[float]:
        resp = self._client.models.embed_content(model=self._model, contents=text)
        if not resp.embeddings or resp.embeddings[0].values is None:
            raise RuntimeError("Gemini embed_content returned no embedding for query")
        return list(resp.embeddings[0].values)


def _make_embeddings() -> _GeminiGenaiEmbeddings:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")
    model = os.getenv("GEMINI_EMBEDDING_MODEL", _DEFAULT_GEMINI_EMBED_MODEL)
    return _GeminiGenaiEmbeddings(api_key=GEMINI_API_KEY, model=model)


def embed_and_store(documents: list[Document], collection_name: str = "sentinelrag_knowledge"):
    """
    Converts semantic chunks into vectors and persists them to ChromaDB.
    Returns the vector store instance for immediate use.
    """
    embeddings = _make_embeddings()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH,
        collection_name=collection_name,
    )

    return vector_store


def get_vector_store(collection_name: str = "sentinelrag_knowledge"):
    """
    Load the existing vector store from disk.
    Used during Query phase to prevent re-embedding
    """
    embeddings = _make_embeddings()

    return Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings,
        collection_name=collection_name,
    )
