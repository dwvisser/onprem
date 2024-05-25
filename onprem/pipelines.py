# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_pipelines.ipynb.

# %% auto 0
__all__ = ['DEFAULT_MAP_PROMPT', 'DEFAULT_REDUCE_PROMPT', 'DEFAULT_BASE_REFINE_PROMPT', 'DEFAULT_REFINE_PROMPT', 'Summarizer',
           'Extractor']

# %% ../nbs/04_pipelines.ipynb 3
import os
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, Callable
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain

from .ingest import load_single_document, load_documents


# %% ../nbs/04_pipelines.ipynb 4
DEFAULT_MAP_PROMPT = """The following is a set of documents
{docs}
Based on this list of docs, please write a concise summary. 
CONCISE SUMMARY:"""

DEFAULT_REDUCE_PROMPT = """The following is set of summaries:
{docs}
Take these and distill it into a final, consolidated summary. 
SUMMARY:"""

DEFAULT_BASE_REFINE_PROMPT = """Write a concise summary of the following:
{text}
CONCISE SUMMARY:"""

DEFAULT_REFINE_PROMPT = (
    "Your job is to produce a final summary\n"
    "We have provided an existing summary up to a certain point: {existing_answer}\n"
    "We have the opportunity to refine the existing summary"
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{text}\n"
    "------------\n"
    "Given the new context, refine the original summary."
    "If the context isn't useful, return the original summary."
)

# %% ../nbs/04_pipelines.ipynb 5
class Summarizer:
    def __init__(
        self,
        llm,
        prompt_template: Optional[str] = None,              
        map_prompt: Optional[str] = None,
        reduce_prompt: Optional[str] = None,
        refine_prompt: Optional[str] = None, 
        **kwargs,
    ):
        """
        `Summarizer` summarizes one or more documents

        **Args:**

        - *llm*: An `onprem.LLM` object
        - *prompt_template*: A model specific prompt_template with a single placeholder named "{prompt}".
                             All prompts (e.g., Map-Reduce prompts) are wrapped within this prompt.
                             If supplied, overrides the `prompt_template` supplied to the `LLM` constructor.
        - *map_prompt*: Map prompt for Map-Reduce summarization. If None, default is used.
        - *reduce_prompt*: Reduce prompt for Map-Reduce summarization. If None, default is used.
        - *refine_prompt*: Refine prompt for Refine-based summarization. If None, default is used.

        """
        self.llm = llm
        self.prompt_template = prompt_template if prompt_template is not None else llm.prompt_template
        self.map_prompt = map_prompt if map_prompt else DEFAULT_MAP_PROMPT
        self.reduce_prompt = reduce_prompt if reduce_prompt else DEFAULT_REDUCE_PROMPT
        self.refine_prompt = refine_prompt if refine_prompt else DEFAULT_REFINE_PROMPT


    def summarize(self, 
                  fpath:str, 
                  strategy:str='map_reduce',
                  chunk_size:int=1000, 
                  chunk_overlap:int=0, 
                  token_max:int=2000,
                  max_chunks_to_use: Optional[int] = None,
                 ):
        """
        Summarize one or more documents (e.g., PDFs, MS Word, MS Powerpoint, plain text)
        using either Langchain's Map-Reduce strategy or Refine strategy.

        **Args:**

        - *fpath*: A path to either a folder of documents or a single file.
        - *strategy*: One of {'map_reduce', 'refine'}. 
        - *chunk_size*: Number of characters of each chunk to summarize
        - *chunk_overlap*: Number of characters that overlap between chunks
        - *token_max*: Maximum number of tokens to group documents into
        - *max_chunks_to_use*: Maximum number of chunks (starting from beginning) to use.
                               Useful for documents that have abstracts or informative introductions.
                               If None, all chunks are considered for summarizer.

        **Returns:**

        - str: a summary of your documents
        """
          
        if os.path.isfile(fpath):
            docs = load_single_document(fpath)
        else:
            docs = load_documents(fpath)

        if strategy == 'map_reduce':
            summary = self._map_reduce(docs, 
                                      chunk_size=chunk_size, 
                                      chunk_overlap=chunk_overlap, 
                                      token_max=token_max,
                                      max_chunks_to_use=max_chunks_to_use)
        elif strategy == 'refine':
            summary = self._refine(docs, 
                                   chunk_size=chunk_size, 
                                   chunk_overlap=chunk_overlap, 
                                   token_max=token_max,
                                   max_chunks_to_use=max_chunks_to_use)
            
        else:
            raise ValueError(f'Unknown strategy: {self.strategy}')
        return summary

    
    def _map_reduce(self, docs, chunk_size=1000, chunk_overlap=0, token_max=1000, 
                    max_chunks_to_use = None, **kwargs):
        """ Map-Reduce summarization"""
        langchain_llm = self.llm.llm

        # Map
        # map_template = """The following is a set of documents
        # {docs}
        # Based on this list of docs, please identify the main themes 
        # Helpful Answer:"""
        # map_template = """The following is a set of documents
        # {docs}
        # Based on this list of docs, please write a concise summary.
        # CONCISE SUMMARY:"""
        map_template = self.map_prompt
        if self.prompt_template: 
            map_template = self.prompt_template.format(**{'prompt':map_template})
        map_prompt = PromptTemplate.from_template(map_template)
        map_chain = LLMChain(llm=langchain_llm, prompt=map_prompt)

        # Reduce
        # reduce_template = """The following is set of summaries:
        # {docs}
        # Take these and distill it into a final, consolidated summary. 
        # SUMMARY:"""
        reduce_template = self.reduce_prompt
        if self.prompt_template:
            reduce_template = self.prompt_template.format(**{'prompt':reduce_template})
        reduce_prompt = PromptTemplate.from_template(reduce_template)

        # Run chain
        reduce_chain = LLMChain(llm=langchain_llm, prompt=reduce_prompt)
        
        # Takes a list of documents, combines them into a single string, and passes this to an LLMChain
        combine_documents_chain = StuffDocumentsChain(
            llm_chain=reduce_chain, document_variable_name="docs"
        )
        
        # Combines and iteravely reduces the mapped documents
        reduce_documents_chain = ReduceDocumentsChain(
            # This is final chain that is called.
            combine_documents_chain=combine_documents_chain,
            # If documents exceed context for `StuffDocumentsChain`
            collapse_documents_chain=combine_documents_chain,
            # The maximum number of tokens to group documents into.
            token_max=token_max)

        # Combining documents by mapping a chain over them, then combining results
        map_reduce_chain = MapReduceDocumentsChain(
            # Map chain
            llm_chain=map_chain,
            # Reduce chain
            reduce_documents_chain=reduce_documents_chain,
            # The variable name in the llm_chain to put the documents in
            document_variable_name="docs",
            # Return the results of the map steps in the output
            return_intermediate_steps=False,
        )
        
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        split_docs = text_splitter.split_documents(docs)
        split_docs = split_docs[:max_chunks_to_use] if max_chunks_to_use else split_docs

        return map_reduce_chain.invoke(split_docs)

    def _refine(self, docs, chunk_size=1000, chunk_overlap=0, 
                max_chunks_to_use = None, **kwargs):
        """ Refine summarization"""

        # initial_template = """Write a concise summary of the following:
        # {text}
        # CONCISE SUMMARY:"""
        initial_template = self.refine_base_prompt
        if self.prompt_template:
            initial_template = self.prompt_template.format(**{'prompt':initial_template})
        prompt = PromptTemplate.from_template(initial_template)
        
        # refine_template = (
        #     "Your job is to produce a final summary\n"
        #     "We have provided an existing summary up to a certain point: {existing_answer}\n"
        #     "We have the opportunity to refine the existing summary"
        #     "(only if needed) with some more context below.\n"
        #     "------------\n"
        #     "{text}\n"
        #     "------------\n"
        #     "Given the new context, refine the original summary."
        #     "If the context isn't useful, return the original summary."
        # )
        refine_template = self.refine_prompt
        if self.prompt_template:
            refine_template = self.prompt_template.format(**{'prompt':refine_template})
        refine_prompt = PromptTemplate.from_template(refine_template)
        chain = load_summarize_chain(
            llm=self.llm.llm,
            chain_type="refine",
            question_prompt=prompt,
            refine_prompt=refine_prompt,
            return_intermediate_steps=True,
            input_key="input_documents",
            output_key="output_text",
        )
        
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        split_docs = text_splitter.split_documents(docs)
        split_docs = split_docs[:max_chunks_to_use] if max_chunks_to_use else split_docs
        result = chain({"input_documents": split_docs}, return_only_outputs=True)
        print(result)
        return result['output_text']
        

# %% ../nbs/04_pipelines.ipynb 7
from syntok import segmenter
import textwrap
import pandas as pd

class Extractor:
    def __init__(
        self,
        llm,
        prompt_template: Optional[str] = None,              
        **kwargs,
    ):
        """
        `Extractor` applies a given prompt to each sentence or paragraph in a document and returns the results.

        **Args:**

        - *llm*: An `onprem.LLM` object
        - *prompt_template*: A model specific prompt_template with a single placeholder named "{prompt}".
                             All prompts (e.g., Map-Reduce prompts) are wrapped within this prompt.
                             If supplied, overrides the `prompt_template` supplied to the `LLM` constructor.

        """
        self.llm = llm
        self.prompt_template = prompt_template if prompt_template is not None else llm.prompt_template



    def apply(self,
              ex_prompt_template:str, 
              fpath: Optional[str] = None,
              content: Optional[str] = None,
              unit:str='paragraph',
              filter_fn: Optional[Callable] = None,
              pdf_pages:List[int]=[],
              maxchars = 2048,
              stop:list=[]
             ):
        """
        Apply the prompt to each `unit` (where a "unit" is either a paragraph or sentence) optionally filtered by `filter_fn`.
        Results are stored in a `pandas.Dataframe`.


        **Args:**

        - *ex_prompt_template*: A prompt to apply to each `unit` in document. Should have a single variable, `{text}`.
                               Example: `"Extract universities from the following text delimited by ###:\n\n###{text}###"`
        - *fpath*: A path to to a single file of interest (e.g., a PDF or MS Word document). Mutually-exclusive with `content`.
        - *content*: Text content of a document of interest.  Mutually-exclusive with `fpath`.
        - *unit*: One of {'sentence', 'paragraph'}. 
        - *filter_fn*: A function that accepts a sentence or paragraph and returns `True` if prompt should be applied to it.
                       If `filter_fn` returns False, the text is ignored and excluded from results.
        - *pdf_pages*: If `fpath` is a PDF document, only apply prompt to text on page numbers listed in `pdf_pages`.
                       Page numbers start with 1, not 0 (e.g., `pdf_pages=[1,2,3]` for first three pages).
                       If list is empty, prompt is applied to every page.
        - *maxchars*: units (i.e., paragraphs or sentences) larger than `maxhcars` split.
        - *stop*: list of characters to trigger the LLM to stop generating.



        **Returns:**

        - pd.Dataframe: a Dataframe with results
        """
        if not(bool(fpath) != bool(content)):
            raise ValueError('Either fpath argument or content argument must be supplied but not both.')
            
        # setup extraction prompt
        extraction_prompt = ex_prompt_template if self.prompt_template is None else self.prompt_template.format(**{'prompt': ex_prompt_template})   

        # extract text
        if not content:
            if not os.path.isfile(fpath):
                raise ValueError(f'{fpath} is not a file')
            docs = load_single_document(fpath)
            ext = "." + fpath.rsplit(".", 1)[-1].lower()
            if ext == '.pdf' and pdf_pages:
                docs = [doc for i,doc in enumerate(docs) if i+1 in pdf_pages]
            content = '\n\n'.join([doc.page_content for doc in docs])
        
        # segment
        chunks = self.segment(content)
        extractions = []
        texts = []
        for chunk in chunks:
            if filter_fn and not filter_fn(chunk): continue
            prompt = extraction_prompt.format(text=chunk)
            extractions.append(self.llm.prompt(prompt, stop=stop))
            texts.append(chunk)
        df = pd.DataFrame({'Extractions':extractions, 'Texts':texts})
        return df
            
        return results


    def segment(self, text:str, unit:str='paragraph', maxchars:int=2048):
        """
        Segments text into a list of paragraphs or sentences depending on value of `unit`.
        """
        units = []
        for paragraph in segmenter.analyze(text):
            sentences = []
            for sentence in paragraph:
                text = ""
                for token in sentence:
                    text += f'{token.spacing}{token.value}'
                sentences.append(text)
            if unit == 'sentence':
                units.extend(sentences)
            else:
                units.append(" ".join(sentences))
        chunks = []
        for s in units:
            parts = textwrap.wrap(s, maxchars, break_long_words=False)
            chunks.extend(parts)
        return chunks
