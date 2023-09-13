# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['DEFAULT_MODEL_URL', 'DEFAULT_LARGER_URL', 'DEFAULT_EMBEDDING_MODEL', 'DEFAULT_QA_PROMPT', 'LLM']

# %% ../nbs/00_core.ipynb 3
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import LlamaCpp
from langchain.prompts import PromptTemplate
import chromadb
import os
import warnings
from typing import Any, Dict, Generator, List, Optional, Tuple, Union


# %% ../nbs/00_core.ipynb 4
from . import utils as U
DEFAULT_MODEL_URL = 'https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGML/resolve/main/Wizard-Vicuna-7B-Uncensored.ggmlv3.q4_0.bin'
DEFAULT_LARGER_URL = ' https://huggingface.co/TheBloke/WizardLM-13B-V1.2-GGML/resolve/main/wizardlm-13b-v1.2.ggmlv3.q4_0.bin'
DEFAULT_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
DEFAULT_QA_PROMPT = """"Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:"""

class LLM:
    def __init__(self, 
                 model_url=DEFAULT_MODEL_URL,
                 use_larger:bool=False,
                 n_gpu_layers:Optional[int]=None, 
                 model_download_path:Optional[str]=None,
                 vectordb_path:Optional[str]=None,
                 max_tokens:int=512, 
                 n_ctx:int=2048, 
                 n_batch:int=1024,
                 mute_stream:bool=False,
                 embedding_model_name:str ='sentence-transformers/all-MiniLM-L6-v2',
                 embedding_model_kwargs:dict ={'device': 'cpu'},
                 embedding_encode_kwargs:dict ={'normalize_embeddings': False},
                 confirm:bool=True,
                 verbose:bool=False,
                 **kwargs):
        """
        LLM Constructor.  Extra `kwargs` are fed directly to `langchain.llms.LlamaCpp`.
        
        **Args:**

        - *model_url*: URL to `.bin` model (currently must be GGML model).
        - *use_larger*: If True, a larger model than the default `model_url` will be used.
        - *n_gpu_layers*: Number of layers to be loaded into gpu memory. Default is `None`.
        - *model_download_path*: Path to download model. Default is `onprem_data` in user's home directory.
        - *vectordb_path*: Path to vector database (created if it doesn't exist). 
                           Default is `onprem_data/vectordb` in user's home directory.
        - *max_tokens*: The maximum number of tokens to generate.
        - *n_ctx*: Token context window.
        - *n_batch*: Number of tokens to process in parallel.
        - *mute_stream*: Mute ChatGPT-like token stream output during generation
        - *embedding_model*: name of sentence-transformers model. Used for `LLM.ingest` and `LLM.ask`.
        - *embedding_model_kwargs*: arguments to embedding model (e.g., `{device':'cpu'}`).
        - *embedding_encode_kwargs*: arguments to encode method of 
                                     embedding model (e.g., `{'normalize_embeddings': False}`).
        - *confirm*: whether or not to confirm with user before downloading a model
        - *verbose*: Verbosity
        """
        self.model_url = DEFAULT_LARGER_URL if use_larger else model_url
        if verbose:
            print(f'Since use_larger=True, we are using: {os.path.basename(DEFAULT_LARGER_URL)}')
        self.model_name = os.path.basename(self.model_url)
        self.model_download_path = model_download_path or U.get_datadir()
        if not os.path.isfile(os.path.join(self.model_download_path, self.model_name)):
            self.download_model(self.model_url, model_download_path=self.model_download_path, confirm=confirm)
        self.vectordb_path = vectordb_path
        self.llm = None
        self.ingester = None
        self.n_gpu_layers = n_gpu_layers
        self.max_tokens = max_tokens
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.callbacks = [] if mute_stream else [StreamingStdOutCallbackHandler()]
        self.embedding_model_name = embedding_model_name
        self.embedding_model_kwargs = embedding_model_kwargs
        self.embedding_encode_kwargs = embedding_encode_kwargs
        self.verbose = verbose
        self.extra_kwargs = kwargs
 
    @classmethod
    def download_model(cls, model_url:str=DEFAULT_MODEL_URL, 
                       model_download_path:Optional[str]=None, 
                       confirm:bool=True, 
                       ssl_verify:bool=True):
        """
        Download an LLM in GGML format supported by [lLama.cpp](https://github.com/ggerganov/llama.cpp).
        
        **Args:**
        
        - *model_url*: URL of model
        - *model_download_path*: Path to download model. Default is `onprem_data` in user's home directory.
        - *confirm*: whether or not to confirm with user before downloading
        - *ssl_verify*: If True, SSL certificates are verified. 
                        You can set to False if corporate firewall gives you problems.
        """
        datadir = model_download_path or U.get_datadir()
        model_name = os.path.basename(model_url)
        filename = os.path.join(datadir, model_name)
        confirm_msg = f"You are about to download the LLM {model_name} to the {datadir} folder. Are you sure?"
        if os.path.isfile(filename):
            confirm_msg = f'There is already a file {model_name} in {datadir}.\n Do you want to still download it?'
            
        shall = True
        if confirm:
            shall = input("%s (y/N) " % confirm_msg).lower() == "y"
        if shall:
            U.download(model_url, filename, verify=ssl_verify)
        else:
            warnings.warn(f'{model_name} was not downloaded because "Y" was not selected.')
        return

    def load_ingester(self):
        """
        Get `Ingester` instance. 
        You can access the `langchain.vectorstores.Chroma` instance with `load_ingester().get_db()`.
        """
        if not self.ingester:
            from onprem.ingest import Ingester
            self.ingester = Ingester(embedding_model_name=self.embedding_model_name,
                                     embedding_model_kwargs=self.embedding_model_kwargs,
                                     embedding_encode_kwargs=self.embedding_encode_kwargs,
                                     persist_directory=self.vectordb_path)
        return self.ingester
        
        
    def ingest(self, 
               source_directory:str,
               chunk_size:int=500,
               chunk_overlap:int=50
              ):
        """
        Ingests all documents in `source_folder` into vector database.
        Previously-ingested documents are ignored.

        **Args:**
        
        - *source_directory*: path to folder containing document store
        - *chunk_size*: text is split to this many characters by `langchain.text_splitter.RecursiveCharacterTextSplitter`
        - *chunk_overlap*: character overlap between chunks in `langchain.text_splitter.RecursiveCharacterTextSplitter`
        
        **Returns:** `None`
        """
        ingester = self.load_ingester()
        ingester.ingest(source_directory, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return

 
        
    def check_model(self):
        """
        Returns the path to the model
        """
        datadir = self.model_download_path
        model_path = os.path.join(datadir, self.model_name)
        if not os.path.isfile(model_path):
            raise ValueError(f'The LLM model {self.model_name} does not appear to have been downloaded. '+\
                             f'Execute the download_model() method to download it.')
        return model_path
        
 
    def load_llm(self):
        """
        Loads the LLM from the model path.
        """
        model_path = self.check_model()
        
        if not self.llm:
            self.llm =  llm = LlamaCpp(model_path=model_path, 
                                       max_tokens=self.max_tokens, 
                                       n_batch=self.n_batch, 
                                       callbacks=self.callbacks, 
                                       verbose=self.verbose, 
                                       n_gpu_layers=self.n_gpu_layers, 
                                       n_ctx=self.n_ctx, **self.extra_kwargs)    

        return self.llm
        
        
    def prompt(self, prompt, prompt_template:Optional[str]=None):
        """
        Send prompt to LLM to generate a response
        
        **Args:**
        
        - *prompt*: The prompt to supply to the model
        - *prompt_template*: Optional prompt template (must have a variable named "prompt")
        """
        llm = self.load_llm()
        if prompt_template:
            prompt = prompt_template.format(**{'prompt': prompt})
        return llm(prompt)  
 

    def load_qa(self, num_source_docs:int=4, prompt_template:str=DEFAULT_QA_PROMPT):
        """
        Prepares and loads the `langchain.chains.RetrievalQA` object
        
        **Args:**
        
        - *num_source_docs*: the number of ingested source documents use to generate answer
        - *prompt_template*: A string representing the prompt with variables "context" and "question"      
        """
        ingester = self.load_ingester()
        db = ingester.get_db()
        if not db:
            raise ValueError('A vector database has not yet been created. Please call the LLM.ingest method.')
        retriever = db.as_retriever(search_kwargs={"k": num_source_docs})
        llm = self.load_llm()
        PROMPT = PromptTemplate(
                    template=prompt_template, input_variables=["context", "question"])
        qa = RetrievalQA.from_chain_type(llm=llm, 
                                         chain_type="stuff", 
                                         retriever=retriever, 
                                         return_source_documents= True,
                                         chain_type_kwargs={'prompt':PROMPT})
        return qa

    
    def ask(self, question:str, num_source_docs:int=4, prompt_template=DEFAULT_QA_PROMPT):
        """
        Answer a question based on source documents fed to the `ingest` method.
        
        **Args:**
        
        - *question*: a question you want to ask
        - *num_source_docs*: the number of ingested source documents use to generate answer
        - *prompt_template*: A string representing the prompt with variables "context" and "question"
        """
        qa = self.load_qa(num_source_docs=num_source_docs, prompt_template=prompt_template)
        res = qa(question)
        return res['result'], res['source_documents']
