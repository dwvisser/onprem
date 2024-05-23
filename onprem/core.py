# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['DEFAULT_MODEL_URL', 'DEFAULT_LARGER_URL', 'DEFAULT_EMBEDDING_MODEL', 'DEFAULT_QA_PROMPT',
           'AnswerConversationBufferMemory', 'LLM']

# %% ../nbs/00_core.ipynb 3
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import LlamaCpp
from langchain_openai import ChatOpenAI
import chromadb
import os
import warnings
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, Callable

# %% ../nbs/00_core.ipynb 4
# reference: https://github.com/langchain-ai/langchain/issues/5630#issuecomment-1574222564
class AnswerConversationBufferMemory(ConversationBufferMemory):
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        return super(AnswerConversationBufferMemory, self).save_context(
            inputs, {"response": outputs["answer"]}
        )

# %% ../nbs/00_core.ipynb 5
from . import utils as U

DEFAULT_MODEL_URL = "https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGUF/resolve/main/Wizard-Vicuna-7B-Uncensored.Q4_K_M.gguf"
DEFAULT_LARGER_URL = "https://huggingface.co/TheBloke/WizardLM-13B-V1.2-GGUF/resolve/main/wizardlm-13b-v1.2.Q4_K_M.gguf"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_QA_PROMPT = """"Use the following pieces of context delimited by three backticks to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

```{context}```

Question: {question}
Helpful Answer:"""


class LLM:
    def __init__(
        self,
        model_url=DEFAULT_MODEL_URL,
        use_larger: bool = False,
        n_gpu_layers: Optional[int] = None,
        prompt_template: Optional[str] = None,
        model_download_path: Optional[str] = None,
        vectordb_path: Optional[str] = None,
        max_tokens: int = 512,
        n_ctx: int = 3900,
        n_batch: int = 1024,
        stop:list=[],
        mute_stream: bool = False,
        callbacks=[],
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        embedding_model_kwargs: dict = {"device": "cpu"},
        embedding_encode_kwargs: dict = {"normalize_embeddings": False},
        rag_num_source_docs: int = 4,
        rag_score_threshold: float = 0.0,
        confirm: bool = True,
        verbose: bool = True,
        **kwargs,
    ):
        """
        LLM Constructor.  Extra `kwargs` are fed directly to `langchain.llms.LlamaCpp`.

        **Args:**

        - *model_url*: URL to `.GGUF` model (or the filename if already been downloaded to `model_download_path`).
                       To use a non-local OpenAI model instead, replace URL with: `openai://<name_of_model>` 
                       (e.g., `openai://gpt-3.5-turbo`).
        - *use_larger*: If True, a larger model than the default `model_url` will be used.
        - *n_gpu_layers*: Number of layers to be loaded into gpu memory. Default is `None`.
        - *prompt_template*: Optional prompt template (must have a variable named "prompt").
        - *model_download_path*: Path to download model. Default is `onprem_data` in user's home directory.
        - *vectordb_path*: Path to vector database (created if it doesn't exist).
                           Default is `onprem_data/vectordb` in user's home directory.
        - *max_tokens*: The maximum number of tokens to generate.
        - *n_ctx*: Token context window. (Llama2 models have max of 4096.)
        - *n_batch*: Number of tokens to process in parallel.
        - *stop*: a list of strings to stop generation when encountered (applied to all calls to `LLM.prompt`)
        - *mute_stream*: Mute ChatGPT-like token stream output during generation
        - *callbacks*: Callbacks to supply model
        - *embedding_model_name*: name of sentence-transformers model. Used for `LLM.ingest` and `LLM.ask`.
        - *embedding_model_kwargs*: arguments to embedding model (e.g., `{device':'cpu'}`).
        - *embedding_encode_kwargs*: arguments to encode method of
                                     embedding model (e.g., `{'normalize_embeddings': False}`).
        - *rag_num_source_docs*: The maximum number of documents retrieved and fed to `LLM.ask` and `LLM.chat` to generate answers
        - *rag_score_threshold*: Minimum similarity score for source to be considered by `LLM.ask` and `LLM.chat`
        - *confirm*: whether or not to confirm with user before downloading a model
        - *verbose*: Verbosity
        """
        self.model_url = DEFAULT_LARGER_URL if use_larger else model_url
        self.model_name = os.path.basename(self.model_url)
        self.model_download_path = model_download_path or U.get_datadir()
        if self.is_local():
            try:
                from llama_cpp import Llama
            except ImportError:
                raise ValueError('To run local LLMs, the llama-cpp-python package is required. ' +\
                                 'You can visit https://python.langchain.com/docs/integrations/llms/llamacpp ' +\
                                 'and follow the instructions for your operating system.')
        if self.is_local() and not os.path.isfile(os.path.join(self.model_download_path, self.model_name)):
            self.download_model(
                self.model_url,
                model_download_path=self.model_download_path,
                confirm=confirm,
            )
        self.prompt_template = prompt_template
        self.vectordb_path = vectordb_path
        self.llm = None
        self.ingester = None
        self.qa = None
        self.chatqa = None
        self.n_gpu_layers = n_gpu_layers
        self.max_tokens = max_tokens
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.stop = stop
        self.mute_stream = mute_stream
        self.callbacks = [] if mute_stream else [StreamingStdOutCallbackHandler()]
        if callbacks:
            self.callbacks.extend(callbacks)
        self.embedding_model_name = embedding_model_name
        self.embedding_model_kwargs = embedding_model_kwargs
        self.embedding_encode_kwargs = embedding_encode_kwargs
        self.rag_num_source_docs = rag_num_source_docs
        self.rag_score_threshold = rag_score_threshold
        self.verbose = verbose
        self.extra_kwargs = kwargs


        # explicitly set offload_kqv
        # reference: https://github.com/abetlen/llama-cpp-python/issues/999#issuecomment-1858041458
        self.offload_kqv = True if n_gpu_layers is not None and n_gpu_layers > 0 else False

        # load LLM
        self.load_llm()

        # issue warning
        if self.is_openai_model():
            warnings.warn(f'The model you supplied is {self.model_name}, an external service (i.e., not on-premises). '+\
                          f'Use with caution, as your data and prompts will be sent externally.')

    def is_openai_model(self):
        return self.model_url.lower().startswith('openai')


    def is_local_api(self):
        basename = os.path.basename(self.model_url)
        return self.model_url.lower().startswith('http') and not basename.lower().endswith('.gguf') and not basename.lower().endswith('.bin')

    def is_local(self):
        return not self.is_openai_model() and not self.is_local_api()

    def update_max_tokens(self, value:int=512):
        """
        Update `max_tokens` (maximum length of generation).
        """
        llm = self.load_llm()
        llm.max_tokens = value


    def update_stop(self, value:list=[]):
        """
        Update `max_tokens` (maximum length of generation).
        """
        llm = self.load_llm()
        llm.stop = value


    @classmethod
    def download_model(
        cls,
        model_url: str = DEFAULT_MODEL_URL,
        model_download_path: Optional[str] = None,
        confirm: bool = True,
        ssl_verify: bool = True,
    ):
        """
        Download an LLM in GGML format supported by [lLama.cpp](https://github.com/ggerganov/llama.cpp).

        **Args:**

        - *model_url*: URL of model
        - *model_download_path*: Path to download model. Default is `onprem_data` in user's home directory.
        - *confirm*: whether or not to confirm with user before downloading
        - *ssl_verify*: If True, SSL certificates are verified.
                        You can set to False if corporate firewall gives you problems.
        """
        if 'https://huggingface.co' in model_url and 'resolve' not in model_url:
            warnings.warn('\n\nThe supplied URL may not be pointing to the actual GGUF model file.  Please check it.\n\n')
        datadir = model_download_path or U.get_datadir()
        model_name = os.path.basename(model_url)
        filename = os.path.join(datadir, model_name)
        confirm_msg = f"\nYou are about to download the LLM {model_name} to the {datadir} folder. Are you sure?"
        if os.path.isfile(filename):
            confirm_msg = f"There is already a file {model_name} in {datadir}.\n Do you want to still download it?"

        shall = True
        if confirm:
            shall = input("%s (y/N) " % confirm_msg).lower() == "y"
        if shall:
            U.download(model_url, filename, verify=ssl_verify)
        else:
            warnings.warn(
                f'{model_name} was not downloaded because "Y" was not selected.'
            )
        return

    def load_ingester(self):
        """
        Get `Ingester` instance.
        You can access the `langchain.vectorstores.Chroma` instance with `load_ingester().get_db()`.
        """
        if not self.ingester:
            from onprem.ingest import Ingester

            self.ingester = Ingester(
                embedding_model_name=self.embedding_model_name,
                embedding_model_kwargs=self.embedding_model_kwargs,
                embedding_encode_kwargs=self.embedding_encode_kwargs,
                persist_directory=self.vectordb_path,
            )
        return self.ingester

    def load_vectordb(self):
        """
        Get Chroma db instance
        """
        ingester = self.load_ingester()
        db = ingester.get_db()
        if not db:
            raise ValueError(
                "A vector database has not yet been created. Please call the LLM.ingest method."
            )
        return db

    def ingest(
        self, source_directory: str, chunk_size: int = 500, chunk_overlap: int = 50, ignore_fn:Optional[Callable] = None
    ):
        """
        Ingests all documents in `source_folder` into vector database.
        Previously-ingested documents are ignored.

        **Args:**

        - *source_directory*: path to folder containing document store
        - *chunk_size*: text is split to this many characters by `langchain.text_splitter.RecursiveCharacterTextSplitter`
        - *chunk_overlap*: character overlap between chunks in `langchain.text_splitter.RecursiveCharacterTextSplitter`
        - *ignore_fn*: Optional function that accepts the file path (including file name) as input and returns True
                       if file path should not be ingested.

        **Returns:** `None`
        """
        ingester = self.load_ingester()
        return ingester.ingest(
            source_directory, chunk_size=chunk_size, chunk_overlap=chunk_overlap, ignore_fn=ignore_fn
        )

    def check_model(self):
        """
        Returns the path to the model
        """
        if not self.is_local(): return None
        datadir = self.model_download_path
        model_path = os.path.join(datadir, self.model_name)
        if not os.path.isfile(model_path):
            raise ValueError(
                f"The LLM model {self.model_name} does not appear to have been downloaded. "
                + f"Execute the download_model() method to download it."
            )
        return model_path

    def load_llm(self):
        """
        Loads the LLM from the model path.
        """
        model_path = self.check_model()

        if not self.llm and self.is_openai_model():
            self.llm = ChatOpenAI(model_name=self.model_name, 
                                  callback_manager=CallbackManager(self.callbacks), 
                                  streaming=not self.mute_stream,
                                  max_tokens=self.max_tokens,
                                  **self.extra_kwargs)
        elif not self.llm and self.is_local_api():
            self.llm = ChatOpenAI(base_url=self.model_url,
                                  #model_name=self.model_name, 
                                  callback_manager=CallbackManager(self.callbacks), 
                                  streaming=not self.mute_stream,
                                  max_tokens=self.max_tokens,
                                  **self.extra_kwargs)
        elif not self.llm:
            self.llm = LlamaCpp(
                model_path=model_path,
                max_tokens=self.max_tokens,
                n_batch=self.n_batch,
                callback_manager=CallbackManager(self.callbacks),
                verbose=self.verbose,
                n_gpu_layers=self.n_gpu_layers,
                n_ctx=self.n_ctx,
                offload_kqv = self.offload_kqv,
                **self.extra_kwargs,
            )

        return self.llm


    def prompt(self, prompt, prompt_template: Optional[str] = None, stop:list=[], **kwargs):
        """
        Send prompt to LLM to generate a response.
        Extra keyword arguments are sent directly to the model invocation.

        **Args:**

        - *prompt*: The prompt to supply to the model
        - *prompt_template*: Optional prompt template (must have a variable named "prompt").
                             This value will override any `prompt_template` value supplied 
                             to `LLM` constructor.
        - *stop*: a list of strings to stop generation when encountered. 
                  This value will override the `stop` parameter supplied to `LLM` constructor.

        """
        llm = self.load_llm()
        prompt_template = self.prompt_template if prompt_template is None else prompt_template
        if prompt_template:
            prompt = prompt_template.format(**{"prompt": prompt})
        stop = stop if stop else self.stop
        res = llm.invoke(prompt, stop=stop, **kwargs)
        return res.content if self.is_openai_model() else res



    def load_qa(self, prompt_template: str = DEFAULT_QA_PROMPT):
        """
        Prepares and loads the `langchain.chains.RetrievalQA` object

        **Args:**

        - *prompt_template*: A string representing the prompt with variables "context" and "question"
        """
        if self.qa is None:
            db = self.load_vectordb()
            retriever = db.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": self.rag_num_source_docs,
                    "score_threshold": self.rag_score_threshold,
                },
            )
            llm = self.load_llm()
            PROMPT = PromptTemplate(
                template=prompt_template, input_variables=["context", "question"]
            )
            self.qa = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT},
            )
        return self.qa

    def load_chatqa(self):
        """
        Prepares and loads a `langchain.chains.ConversationalRetrievalChain` instance
        """
        if self.chatqa is None:
            db = self.load_vectordb()
            retriever = db.as_retriever(
                search_type="similarity_score_threshold",  # see note in constructor
                search_kwargs={
                    "k": self.rag_num_source_docs,
                    "score_threshold": self.rag_score_threshold,
                },
            )
            llm = self.load_llm()
            memory = AnswerConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )
            self.chatqa = ConversationalRetrievalChain.from_llm(
                self.llm, retriever, memory=memory, return_source_documents=True
            )
        return self.chatqa

    def ask(self, question: str, qa_template=DEFAULT_QA_PROMPT, prompt_template=None, **kwargs):
        """
        Answer a question based on source documents fed to the `ingest` method.
        Extra keyword arguments are sent directly to the model invocation.

        **Args:**

        - *question*: a question you want to ask
        - *qa_template*: A string representing the prompt with variables "context" and "question"
        - *prompt_template*: the model-specific template in which everything (including QA template) should be wrapped.
                            Should have a single variable "{prompt}". Overrides the `prompt_template` parameter supplied to 
                            `LLM` constructor.

        **Returns:**

        - A dictionary with keys: `answer`, `source_documents`, `question`
        """
        prompt_template = self.prompt_template if prompt_template is None else prompt_template
        prompt_template = qa_template if prompt_template is None else prompt_template.format(**{'prompt': qa_template})
        qa = self.load_qa(prompt_template=prompt_template)
        res = qa.invoke(question, **kwargs)
        res["question"] = res["query"]
        del res["query"]
        res["answer"] = res["result"]
        del res["result"]
        return res

    def chat(self, question: str, **kwargs):
        """
        Chat with documents fed to the `ingest` method.
        Unlike `LLM.ask`, `LLM.chat` includes conversational memory.
        Extra keyword arguments are sent directly to the model invocation.

        **Args:**

        - *question*: a question you want to ask

        **Returns:**

        - A dictionary with keys: `answer`, `source_documents`, `question`, `chat_history`
        """
        chatqa = self.load_chatqa()
        res = chatqa.invoke(question, **kwargs)
        return res
