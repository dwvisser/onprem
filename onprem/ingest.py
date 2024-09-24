"""functionality for document ingestion into a vector database for question-answering"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_ingest.ipynb.

# %% auto 0
__all__ = ['logger', 'DEFAULT_CHUNK_SIZE', 'DEFAULT_CHUNK_OVERLAP', 'COLLECTION_NAME', 'CHROMA_MAX', 'LOADER_MAPPING',
           'DEFAULT_DB', 'MyElmLoader', 'load_single_document', 'load_documents', 'process_documents',
           'does_vectorstore_exist', 'batchify_chunks', 'Ingester']

# %% ../nbs/01_ingest.ipynb 3
import os
import os.path
import glob
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, Callable
from dotenv import load_dotenv
from multiprocessing import Pool
from tqdm import tqdm

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    CSVLoader,
    EverNoteLoader,
    TextLoader,
    PyMuPDFLoader,
    UnstructuredPDFLoader,
    UnstructuredEmailLoader,
    UnstructuredEPubLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredODTLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings
from . import utils as U

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logger = logging.getLogger('OnPrem.LLM-ingest')

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
COLLECTION_NAME = "onprem_chroma"
CHROMA_MAX = 41000

# %% ../nbs/01_ingest.ipynb 4
class MyElmLoader(UnstructuredEmailLoader):
    """Wrapper to fallback to text/plain when default does not work"""

    def load(self) -> List[Document]:
        """Wrapper adding fallback for elm without html"""
        try:
            try:
                doc = UnstructuredEmailLoader.load(self)
            except ValueError as e:
                if "text/html content not found in email" in str(e):
                    # Try plain text
                    self.unstructured_kwargs["content_source"] = "text/plain"
                    doc = UnstructuredEmailLoader.load(self)
                else:
                    raise
        except Exception as e:
            # Add file_path to exception message
            raise type(e)(f"{self.file_path}: {e}") from e

        return doc

# %% ../nbs/01_ingest.ipynb 5
# Map file extensions to document loaders and their arguments
LOADER_MAPPING = {
    ".csv": (CSVLoader, {}),
    ".doc": (UnstructuredWordDocumentLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".enex": (EverNoteLoader, {}),
    ".eml": (MyElmLoader, {}),
    ".epub": (UnstructuredEPubLoader, {}),
    ".html": (UnstructuredHTMLLoader, {}),
    ".md": (UnstructuredMarkdownLoader, {}),
    ".odt": (UnstructuredODTLoader, {}),
    ".pdf": (PyMuPDFLoader, {}),
    ".pdfOCR": (UnstructuredPDFLoader, {"strategy":"hi_res"}),
    ".ppt": (UnstructuredPowerPointLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}),
    # Add more mappings for other file extensions and loaders as needed
}


def load_single_document(file_path: str, # path to file
                         use_pdf_unstructured:bool=False, # use unstructured for PDF extraction if True
                         **kwargs, # If kwargs include `loader_args` (a dictionary), it is passed directly  to langchain loader.
                         ) -> List[Document]:
    """
    Load a single document. Will attempt to OCR PDFs, if necessary.
    """
    ext = "." + file_path.rsplit(".", 1)[-1].lower()
    if ext in LOADER_MAPPING:
        try:
            loader_class, loader_args = LOADER_MAPPING[ext+f'{"OCR" if use_pdf_unstructured else ""}']
            loader_args = kwargs.get('loader_args', loader_args)
            loader = loader_class(file_path, **loader_args)
            if ext == '.pdf' and not use_pdf_unstructured:
                docs = loader.load()
                if not docs or len(docs[0].page_content) < 32:
                    loader_class, loader_args = LOADER_MAPPING[ext+'OCR']
                    loader = loader_class(file_path, **loader_args)
                    return loader.load()
                return loader.load()
            else:
                return loader.load()

        except Exception as e:
            logger.warning(f'Skipping {file_path} due to error: {str(e)}')
    else:
        logger.warning(f"Skipping {file_path} due to unsupported file extension: '{ext}'")


def load_documents(source_dir: str, # path to folder containing documents
                   ignored_files: List[str] = [], # list of filepaths to ignore
                   ignore_fn:Optional[Callable] = None, # callable that accepts file path and returns True for ignored files
) -> List[Document]:
    """
    Loads all documents from the source documents directory, ignoring specified files
    """
    source_dir = os.path.abspath(source_dir)
    all_files = []
    for ext in LOADER_MAPPING:
        all_files.extend(
            glob.glob(os.path.join(source_dir, f"**/*{ext.lower()}"), recursive=True)
        )
        all_files.extend(
            glob.glob(os.path.join(source_dir, f"**/*{ext.upper()}"), recursive=True)
        )

    filtered_files = [
        file_path for file_path in all_files if file_path not in ignored_files and not os.path.basename(file_path).startswith('~$')
         and (ignore_fn is None or not ignore_fn(file_path))
    ]

    with Pool(processes=os.cpu_count()) as pool:
        results = []
        with tqdm(
            total=len(filtered_files), desc="Loading new documents", ncols=80
        ) as pbar:
            for i, docs in enumerate(
                pool.imap_unordered(load_single_document, filtered_files)
            ):
                if docs is not None: results.extend(docs)
                pbar.update()

    return results


def process_documents(
    source_directory: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ignored_files: List[str] = [],
    ignore_fn:Optional[Callable] = None


) -> List[Document]:
    """
    Load documents and split in chunks

    **Args**:

      - *source_directory*: path to folder containing document store
      - *chunk_size*: text is split to this many characters by `langchain.text_splitter.RecursiveCharacterTextSplitter`
      - *chunk_overlap*: character overlap between chunks in `langchain.text_splitter.RecursiveCharacterTextSplitter`
      - *ignored_files*: list of files to ignore
      - *ignore_fn*: Optional function that accepts the file path (including file name) as input and returns True
                     if file path should not be ingested.

    **Returns:** list of `langchain.docstore.document.Document` objects

    """
    print(f"Loading documents from {source_directory}")
    documents = load_documents(source_directory, ignored_files, ignore_fn=ignore_fn)
    if not documents:
        print("No new documents to load")
        return
    print(f"Loaded {len(documents)} new documents from {source_directory}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    texts = text_splitter.split_documents(documents)
    print(f"Split into {len(texts)} chunks of text (max. {chunk_size} chars each)")
    return texts


def does_vectorstore_exist(db) -> bool:
    """
    Checks if vectorstore exists
    """
    if not db.get()["documents"]:
        return False
    return True


def batchify_chunks(texts):
    split_docs_chunked = U.split_list(texts, CHROMA_MAX)
    total_chunks = sum(1 for _ in U.split_list(texts, CHROMA_MAX))
    return split_docs_chunked, total_chunks


# %% ../nbs/01_ingest.ipynb 6
from .utils import get_datadir

os.environ["TOKENIZERS_PARALLELISM"] = "0"
DEFAULT_DB = "vectordb"


class Ingester:
    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        embedding_model_kwargs: dict = {"device": "cpu"},
        embedding_encode_kwargs: dict = {"normalize_embeddings": False},
        persist_directory: Optional[str] = None,
    ):
        """
        Ingests all documents in `source_folder` (previously-ingested documents are ignored)

        **Args**:

          - *embedding_model*: name of sentence-transformers model
          - *embedding_model_kwargs*: arguments to embedding model (e.g., `{device':'cpu'}`)
          - *embedding_encode_kwargs*: arguments to encode method of
                                       embedding model (e.g., `{'normalize_embeddings': False}`).
          - *persist_directory*: Path to vector database (created if it doesn't exist).
                                 Default is `onprem_data/vectordb` in user's home directory.


        **Returns**: `None`
        """
        self.persist_directory = persist_directory or os.path.join(
            get_datadir(), DEFAULT_DB
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model_name,
            model_kwargs=embedding_model_kwargs,
            encode_kwargs=embedding_encode_kwargs,
        )
        self.chroma_settings = Settings(
            persist_directory=self.persist_directory, anonymized_telemetry=False
        )
        self.chroma_client = chromadb.PersistentClient(
            settings=self.chroma_settings, path=self.persist_directory
        )
        return

    def get_db(self):
        """
        Returns an instance to the `langchain.vectorstores.Chroma` instance
        """
        db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            client_settings=self.chroma_settings,
            client=self.chroma_client,
            collection_metadata={"hnsw:space": "cosine"},
            collection_name=COLLECTION_NAME,
        )
        return db if does_vectorstore_exist(db) else None

    def get_embedding_model(self):
        """
        Returns an instance to the `langchain.embeddings.huggingface.HuggingFaceEmbeddings` instance
        """
        return self.embeddings


    def get_ingested_files(self):
        """
        Returns a list of files previously added to vector database (typically via `LLM.ingest`)
        """
        return set([d['source'] for d in self.get_db().get()['metadatas']])


    def store_documents(self, documents):
        """
        Stores instances of `langchain_core.documents.base.Document` in vectordb
        """
        if not documents: return
        db = self.get_db()
        if db:
            print(f"Creating embeddings. May take some minutes...")
            chunk_batches, total_chunks = batchify_chunks(documents)
            for lst in tqdm(chunk_batches, total=total_chunks):
                db.add_documents(lst)
        else:
            chunk_batches, total_chunks = batchify_chunks(documents)
            print(f"Creating embeddings. May take some minutes...")
            db = None

            for lst in tqdm(chunk_batches, total=total_chunks):
                if not db:
                    db = Chroma.from_documents(
                        lst,
                        self.embeddings,
                        persist_directory=self.persist_directory,
                        client_settings=self.chroma_settings,
                        client=self.chroma_client,
                        collection_metadata={"hnsw:space": "cosine"},
                        collection_name=COLLECTION_NAME,
                    )
                else:
                    db.add_documents(lst)
        return


    def ingest(
        self,
        source_directory: str, # path to folder containing document store
        chunk_size: int = DEFAULT_CHUNK_SIZE, # text is split to this many characters by [langchain.text_splitter.RecursiveCharacterTextSplitter](https://api.python.langchain.com/en/latest/character/langchain_text_splitters.character.RecursiveCharacterTextSplitter.html)
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP, # character overlap between chunks in `langchain.text_splitter.RecursiveCharacterTextSplitter`
        ignore_fn:Optional[Callable] = None # Optional function that accepts the file path (including file name) as input and returns `True` if file path should not be ingested.
    ) -> None:
        """
        Ingests all documents in `source_directory` (previously-ingested documents are
        ignored). When retrieved, the
        [Document](https://api.python.langchain.com/en/latest/documents/langchain_core.documents.base.Document.html)
        objects will each have a `metadata` dict with the absolute path to the file
        in `metadata["source"]`.
        """

        if not os.path.exists(source_directory):
            raise ValueError("The source_directory does not exist.")
        elif os.path.isfile(source_directory):
            raise ValueError(
                "The source_directory argument must be a folder, not a file."
            )
        texts = None
        db = self.get_db()
        if db:
            # Update and store locally vectorstore
            print(f"Appending to existing vectorstore at {self.persist_directory}")
            collection = db.get()
            ignored_files=[ metadata["source"] for metadata in collection["metadatas"]]
        else:
            print(f"Creating new vectorstore at {self.persist_directory}")
            ignored_files = []

        texts = process_documents(
            source_directory,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            ignored_files=ignored_files,
            ignore_fn=ignore_fn

        )
        self.store_documents(texts)

        if texts:
            print(
                f"Ingestion complete! You can now query your documents using the LLM.ask or LLM.chat methods"
            )
        db = None
        return
