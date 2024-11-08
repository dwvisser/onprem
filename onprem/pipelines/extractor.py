# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/04_pipelines.extractor.ipynb.

# %% auto 0
__all__ = ['Extractor']

# %% ../../nbs/04_pipelines.extractor.ipynb 3
import os
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, Callable
import pandas as pd
from ..utils import segment

from ..ingest import load_single_document


class Extractor:
    def __init__(
        self,
        llm, # An `onprem.LLM` object
        prompt_template: Optional[str] = None, # A model specific prompt_template with a single placeholder named "{prompt}". If supplied, overrides the `prompt_template` supplied to the `LLM` constructor.
        **kwargs,
    ):
        """
        `Extractor` applies a given prompt to each sentence or paragraph in a document and returns the results.
        """
        self.llm = llm
        self.prompt_template = prompt_template if prompt_template is not None else llm.prompt_template



    def apply(self,
              ex_prompt_template:str, # A prompt to apply to each `unit` in document. Should have a single variable, `{text}`
              fpath: Optional[str] = None, # A path to to a single file of interest (e.g., a PDF or MS Word document). Mutually-exclusive with `content`.
              content: Optional[str] = None, # Text content of a document of interest.  Mutually-exclusive with `fpath`.
              unit:str='paragraph', # One of {'sentence', 'paragraph'}. 
              preproc_fn: Optional[Callable] = None, # Function should accept a text string and returns a new preprocessed input.
              filter_fn: Optional[Callable] = None, # A function that accepts a sentence or paragraph and returns `True` if prompt should be applied to it.
              clean_fn: Optional[Callable] = None, # A function that accepts a sentence or paragraph and returns "cleaned" version of the text. (applied after `filter_fn`)
              pdf_pages:List[int]=[], # If `fpath` is a PDF document, only apply prompt to text on page numbers listed in `pdf_pages` (starts at 1).
              maxchars = 2048, # units (i.e., paragraphs or sentences) larger than `maxchars` split.
              stop:list=[], # list of characters to trigger the LLM to stop generating.
              pdf_use_unstructured:bool=False, # If True, use unstructured package to extract text from PDF.
              **kwargs, # N/A
             ):
        """
        Apply the prompt to each `unit` (where a "unit" is either a paragraph or sentence) optionally filtered by `filter_fn`.
        Extra kwargs fed directly to `langchain_community.document_loaders.pdf.UnstructuredPDFLoader` when pdf_use_unstructured is True.
        Results are stored in a `pandas.Dataframe`.
        """
        if not(bool(fpath) != bool(content)):
            raise ValueError('Either fpath argument or content argument must be supplied but not both.')
        if pdf_pages and pdf_use_unstructured:
            raise ValueError('The parameters pdf_pages and pdf_use_unstructured are mutually exclusive.')
            
        # setup extraction prompt
        extraction_prompt = ex_prompt_template if self.prompt_template is None else self.prompt_template.format(**{'prompt': ex_prompt_template})   

        # extract text
        if not content:
            if not os.path.isfile(fpath):
                raise ValueError(f'{fpath} is not a file')
            docs = load_single_document(fpath, pdf_use_unstructured=pdf_use_unstructured, **kwargs)
            if not docs: return
            ext = "." + fpath.rsplit(".", 1)[-1].lower()
            if ext == '.pdf' and pdf_pages:
                docs = [doc for i,doc in enumerate(docs) if i+1 in pdf_pages]
            content = '\n\n'.join([preproc_fn(doc.page_content) if preproc_fn else doc.page_content for doc in docs])
        
        # segment
        chunks = segment(content, maxchars=maxchars, unit=unit)
        extractions = []
        texts = []
        for chunk in chunks:
            if filter_fn and not filter_fn(chunk): continue
            if clean_fn: chunk = clean_fn(chunk)
            prompt = extraction_prompt.format(text=chunk)
            extractions.append(self.llm.prompt(prompt, stop=stop))
            texts.append(chunk)
        df = pd.DataFrame({'Extractions':extractions, 'Texts':texts})
        return df
            
        return results
