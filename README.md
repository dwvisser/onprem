# OnPrem.LLM


<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

> A tool for running large language models on-premises using non-public
> data

**[OnPrem.LLM](https://github.com/amaiya/onprem)** is a simple Python
package that makes it easier to run large language models (LLMs) on your
own machines using non-public data (possibly behind corporate
firewalls). Inspired largely by the
[privateGPT](https://github.com/imartinez/privateGPT) GitHub repo,
**OnPrem.LLM** is intended to help integrate local LLMs into practical
applications.

The full documentation is [here](https://amaiya.github.io/onprem/).

A Google Colab demo of installing and using **OnPrem.LLM** is
[here](https://colab.research.google.com/drive/1LVeacsQ9dmE1BVzwR3eTLukpeRIMmUqi?usp=sharing).

------------------------------------------------------------------------

*Latest News* 🔥

- \[2024/11\] v0.5.0 released and now includes support for running LLMs
  with Hugging Face
  [transformers](https://github.com/huggingface/transformers) as the
  backend instead of
  [llama.cpp](https://github.com/abetlen/llama-cpp-python). See [this
  example](https://amaiya.github.io/onprem/#using-hugging-face-transformers-instead-of-llama.cpp).

- \[2024/11\] v0.4.0 released and now includes a `default_model`
  parameter to more easily use models like **Llama-3.1** and
  **Zephyr-7B-beta**.

- \[2024/10\] v0.3.0 released and now includes support for
  [concept-focused
  summarization](https://amaiya.github.io/onprem/examples_summarization.html#concept-focused-summarization)

- \[2024/09\] v0.2.0 released and now includes PDF OCR support and
  better PDF table handling.

- \[2024/06\] v0.1.0 of **OnPrem.LLM** has been released. Lots of new
  updates!

  - [Ability to use with any OpenAI-compatible
    API](https://amaiya.github.io/onprem/#connecting-to-llms-served-through-rest-apis)
    (e.g., vLLM, Ollama, OpenLLM, etc.).
  - Pipeline for [information
    extraction](https://amaiya.github.io/onprem/examples_information_extraction.html)
    from raw documents.
  - Pipeline for [few-shot text
    classification](https://amaiya.github.io/onprem/examples_classification.html)
    (i.e., training a classifier on a tiny number of labeled examples)
    along with the ability to explain few-shot predictions.
  - Default model changed to
    [Mistral-7B-Instruct-v0.2](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
  - [API augmentations and bug
    fixes](https://github.com/amaiya/onprem/blob/master/CHANGELOG.md)

------------------------------------------------------------------------

## Install

Once you have [installed
PyTorch](https://pytorch.org/get-started/locally/), you can install
**OnPrem.LLM** with the following steps:

1.  Install **llama-cpp-python** by [visiting this
    site](https://python.langchain.com/docs/integrations/llms/llamacpp#installation)
    and following instructions for your operating system and machine.
    For CPU-based installations (i.e., no GPU acceleration), you can
    simply do: `pip install llama-cpp-python`.

2.  Install **OnPrem.LLM**: `pip install onprem`

For fast GPU-accelerated inference, see [additional instructions
below](https://amaiya.github.io/onprem/#speeding-up-inference-using-a-gpu).
See [the FAQ](https://amaiya.github.io/onprem/#faq), if you experience
issues with
[llama-cpp-python](https://pypi.org/project/llama-cpp-python/)
installation.

**Note:** Installing **llama-cpp-python** is optional if either the
following is true:

- You supply the `model_id` parameter when instantiating an LLM, as
  [shown
  here](https://amaiya.github.io/onprem/#using-hugging-face-transformers-instead-of-llama.cpp).
- You are using **OnPrem.LLM** with an LLM being served through an
  [external REST
  API](https://amaiya.github.io/onprem/#Connecting-to-LLMs-Served-Through-REST-APIs)
  (e.g., vLLM, OpenLLM, Ollama).

## How to Use

### Setup

``` python
from onprem import LLM

llm = LLM()
```

By default, a 7B-parameter model (**Mistral-7B-Instruct-v0.2**) is
downloaded and used. If `default_model='llama'` is supplied, then a
**Llama-3.1-8B-Instsruct** model is automatically downloaded and used
(which is useful if the default Mistral model struggles with a
particular task):

``` python
# Llama 3.1 is downloaded here and the correct prompt template for Llama-3.1 is automatically configured and used
llm = LLM(default_model='llama')
```

Similarly, suppyling `default_model='zephyr`, will use
**Zephyr-7B-beta**. Of course, you can also easily supply the URL to an
LLM of your choosing to
[`LLM`](https://amaiya.github.io/onprem/core.html#llm) (see the [code
generation section
below](https://amaiya.github.io/onprem/#text-to-code-generation) for an
example or the [FAQ](https://amaiya.github.io/onprem/#faq)). Any extra
parameters supplied to
[`LLM`](https://amaiya.github.io/onprem/core.html#llm) are forwarded
directly to `llama-cpp-python`.

### Send Prompts to the LLM to Solve Problems

This is an example of few-shot prompting, where we provide an example of
what we want the LLM to do.

``` python
prompt = """Extract the names of people in the supplied sentences. Here is an example:
Sentence: James Gandolfini and Paul Newman were great actors.
People:
James Gandolfini, Paul Newman
Sentence:
I like Cillian Murphy's acting. Florence Pugh is great, too.
People:"""

saved_output = llm.prompt(prompt)
```

     Cillian Murphy, Florence Pugh.

Additional prompt examples are [shown
here](https://amaiya.github.io/onprem/examples.html).

### Talk to Your Documents

Answers are generated from the content of your documents (i.e.,
[retrieval augmented generation](https://arxiv.org/abs/2005.11401) or
RAG). Here, we will use [GPU
offloading](https://amaiya.github.io/onprem/#speeding-up-inference-using-a-gpu)
to speed up answer generation using the default model. However, the
Zephyr-7B model may perform even better, responds faster, and is used in
our [example
notebook](https://amaiya.github.io/onprem/examples_rag.html).

``` python
from onprem import LLM

llm = LLM(n_gpu_layers=-1)
```

#### Step 1: Ingest the Documents into a Vector Database

``` python
llm.ingest("./sample_data")
```

    Creating new vectorstore at /home/amaiya/onprem_data/vectordb
    Loading documents from ./sample_data
    Loaded 12 new documents from ./sample_data
    Split into 153 chunks of text (max. 500 chars each)
    Creating embeddings. May take some minutes...
    Ingestion complete! You can now query your documents using the LLM.ask or LLM.chat methods

    Loading new documents: 100%|██████████████████████| 3/3 [00:00<00:00, 13.71it/s]
    100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:02<00:00,  2.49s/it]

#### Step 2: Answer Questions About the Documents

``` python
question = """What is  ktrain?"""
result = llm.ask(question)
```

     Ktrain is a low-code machine learning library designed to facilitate the full machine learning workflow from curating and preprocessing inputs to training, tuning, troubleshooting, and applying models. Ktrain is well-suited for domain experts who may have less experience with machine learning and software coding.

The sources used by the model to generate the answer are stored in
`result['source_documents']`:

``` python
print("\nSources:\n")
for i, document in enumerate(result["source_documents"]):
    print(f"\n{i+1}.> " + document.metadata["source"] + ":")
    print(document.page_content)
```


    Sources:


    1.> /home/amaiya/projects/ghub/onprem/nbs/sample_data/1/ktrain_paper.pdf:
    lection (He et al., 2019). By contrast, ktrain places less emphasis on this aspect of au-
    tomation and instead focuses on either partially or fully automating other aspects of the
    machine learning (ML) workﬂow. For these reasons, ktrain is less of a traditional Au-
    2

    2.> /home/amaiya/projects/ghub/onprem/nbs/sample_data/1/ktrain_paper.pdf:
    possible, ktrain automates (either algorithmically or through setting well-performing de-
    faults), but also allows users to make choices that best ﬁt their unique application require-
    ments. In this way, ktrain uses automation to augment and complement human engineers
    rather than attempting to entirely replace them. In doing so, the strengths of both are
    better exploited. Following inspiration from a blog post1 by Rachel Thomas of fast.ai

    3.> /home/amaiya/projects/ghub/onprem/nbs/sample_data/1/ktrain_paper.pdf:
    with custom models and data formats, as well.
    Inspired by other low-code (and no-
    code) open-source ML libraries such as fastai (Howard and Gugger, 2020) and ludwig
    (Molino et al., 2019), ktrain is intended to help further democratize machine learning by
    enabling beginners and domain experts with minimal programming or data science experi-
    4. http://archive.ics.uci.edu/ml/datasets/Twenty+Newsgroups
    6

    4.> /home/amaiya/projects/ghub/onprem/nbs/sample_data/1/ktrain_paper.pdf:
    ktrain: A Low-Code Library for Augmented Machine Learning
    toML platform and more of what might be called a “low-code” ML platform. Through
    automation or semi-automation, ktrain facilitates the full machine learning workﬂow from
    curating and preprocessing inputs (i.e., ground-truth-labeled training data) to training,
    tuning, troubleshooting, and applying models. In this way, ktrain is well-suited for domain
    experts who may have less experience with machine learning and software coding. Where

### Summarization Pipeline

Summarize your raw documents (e.g., PDFs, MS Word) with an LLM.

#### Map-Reduce Summarization

Summarize each chunk in a document and then generate a single summary
from the individual summaries.

``` python
from onprem import LLM
llm = LLM(n_gpu_layers=-1, verbose=False, mute_stream=True) # disabling viewing of intermediate summarization prompts/inferences
```

``` python
from onprem.pipelines import Summarizer
summ = Summarizer(llm)

resp = summ.summarize('sample_data/1/ktrain_paper.pdf', max_chunks_to_use=5) # omit max_chunks_to_use parameter to consider entire document
print(resp['output_text'])
```

     Ktrain is an open-source machine learning library that offers a unified interface for various machine learning tasks. The library supports both supervised and non-supervised machine learning, and includes methods for training models, evaluating models, making predictions on new data, and providing explanations for model decisions. Additionally, the library integrates with various explainable AI libraries such as shap, eli5 with lime, and others to provide more interpretable models.

#### Concept-Focused Summarization

Summarize a large document with respect to a particular concept of
interest.

``` python
from onprem import LLM
from onprem.pipelines import Summarizer
```

``` python
llm = LLM(default_model='zephyr', n_gpu_layers=-1, verbose=False, temperature=0)
summ = Summarizer(llm)
summary, sources = summ.summarize_by_concept('sample_data/1/ktrain_paper.pdf', concept_description="question answering")
```


    The context provided describes the implementation of an open-domain question-answering system using ktrain, a low-code library for augmented machine learning. The system follows three main steps: indexing documents into a search engine, locating documents containing words in the question, and extracting candidate answers from those documents using a BERT model pretrained on the SQuAD dataset. Confidence scores are used to sort and prune candidate answers before returning results. The entire workflow can be implemented with only three lines of code using ktrain's SimpleQA module. This system allows for the submission of natural language questions and receives exact answers, as demonstrated in the provided example. Overall, the context highlights the ease and accessibility of building sophisticated machine learning models, including open-domain question-answering systems, through ktrain's low-code interface.

### Information Extraction Pipeline

Extract information from raw documents (e.g., PDFs, MS Word documents)
with an LLM.

``` python
from onprem import LLM
from onprem.pipelines import Extractor
# Notice that we're using a cloud-based, off-premises model here! See "OpenAI" section below.
llm = LLM(model_url='openai://gpt-3.5-turbo', verbose=False, mute_stream=True, temperature=0) 
extractor = Extractor(llm)
prompt = """Extract the names of research institutions (e.g., universities, research labs, corporations, etc.) 
from the following sentence delimited by three backticks. If there are no organizations, return NA.  
If there are multiple organizations, separate them with commas.
```{text}```
"""
df = extractor.apply(prompt, fpath='sample_data/1/ktrain_paper.pdf', pdf_pages=[1], stop=['\n'])
df.loc[df['Extractions'] != 'NA'].Extractions[0]
```

    /home/amaiya/projects/ghub/onprem/onprem/core.py:159: UserWarning: The model you supplied is gpt-3.5-turbo, an external service (i.e., not on-premises). Use with caution, as your data and prompts will be sent externally.
      warnings.warn(f'The model you supplied is {self.model_name}, an external service (i.e., not on-premises). '+\

    'Institute for Defense Analyses'

### Few-Shot Classification

Make accurate text classification predictions using only a tiny number
of labeled examples.

``` python
# create classifier
from onprem.pipelines import FewShotClassifier
clf = FewShotClassifier(use_smaller=True)

# Fetching data
from sklearn.datasets import fetch_20newsgroups
import pandas as pd
import numpy as np
classes = ["soc.religion.christian", "sci.space"]
newsgroups = fetch_20newsgroups(subset="all", categories=classes)
corpus, group_labels = np.array(newsgroups.data), np.array(newsgroups.target_names)[newsgroups.target]

# Wrangling data into a dataframe and selecting training examples
data = pd.DataFrame({"text": corpus, "label": group_labels})
train_df = data.groupby("label").sample(5)
test_df = data.drop(index=train_df.index)

# X_sample only contains 5 examples of each class!
X_sample, y_sample = train_df['text'].values, train_df['label'].values

# test set
X_test, y_test = test_df['text'].values, test_df['label'].values

# train
clf.train(X_sample,  y_sample, max_steps=20)

# evaluate
print(clf.evaluate(X_test, y_test)['accuracy'])
#output: 0.98

# make predictions
clf.predict(['Elon Musk likes launching satellites.']).tolist()[0]
#output: sci.space
```

### Text to Code Generation

We’ll use the CodeUp LLM by supplying the URL and employing the
particular prompt format this model expects.

``` python
from onprem import LLM

url = "https://huggingface.co/TheBloke/CodeUp-Llama-2-13B-Chat-HF-GGUF/resolve/main/codeup-llama-2-13b-chat-hf.Q4_K_M.gguf"
llm = LLM(url, n_gpu_layers=-1)  # see below for GPU information
```

Setup the prompt based on what [this model
expects](https://huggingface.co/TheBloke/CodeUp-Llama-2-13B-Chat-HF-GGUF#prompt-template-alpaca)
(this is important):

``` python
template = """
Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{prompt}

### Response:"""
```

You can supply the `prompte_template` to either the
[`LLM`](https://amaiya.github.io/onprem/core.html#llm) constructor
(above) or the
[`LLM.prompt`](https://amaiya.github.io/onprem/core.html#llm.prompt)
method. We will do the latter here:

``` python
answer = llm.prompt(
    "Write Python code to validate an email address.", prompt_template=template
)
```


    Here is an example of Python code that can be used to validate an email address:
    ```
    import re

    def validate_email(email):
        # Use a regular expression to check if the email address is in the correct format
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True
        else:
            return False

    # Test the validate_email function with different inputs
    print("Email address is valid:", validate_email("example@example.com"))  # Should print "True"
    print("Email address is invalid:", validate_email("example@"))  # Should print "False"
    print("Email address is invalid:", validate_email("example.com"))  # Should print "False"
    ```
    The code defines a function `validate_email` that takes an email address as input and uses a regular expression to check if the email address is in the correct format. The regular expression checks for an email address that consists of one or more letters, numbers, periods, hyphens, or underscores followed by the `@` symbol, followed by one or more letters, periods, hyphens, or underscores followed by a `.` and two to three letters.
    The function returns `True` if the email address is valid, and `False` otherwise. The code also includes some test examples to demonstrate how to use the function.

Let’s try out the code generated above.

``` python
import re


def validate_email(email):
    # Use a regular expression to check if the email address is in the correct format
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email):
        return True
    else:
        return False


print(validate_email("sam@@openai.com"))  # bad email address
print(validate_email("sam@openai"))  # bad email address
print(validate_email("sam@openai.com"))  # good email address
```

    False
    False
    True

The generated code may sometimes need editing, but this one worked
out-of-the-box.

### Using Hugging Face Transformers Instead of Llama.cpp

By default, the LLM backend employed by **OnPrem.LLM** is
[llama-cpp-python](https://github.com/abetlen/llama-cpp-python), which
requires models in [GGUF format](https://huggingface.co/docs/hub/gguf).
As of v0.5.0, it is now possible to use [Hugging Face
transformers](https://github.com/huggingface/transformers) as the LLM
backend instead. This is accomplished by using the `model_id` parameter
(instead of supplying a `model_url` argument). In the example below, we
run the
[Zephyr-7B-beta](https://huggingface.co/HuggingFaceH4/zephyr-7b-beta)
model.

``` python
# llama-cpp-python does NOT need to be installed when using model_id parameter
llm = LLM(model_id="HuggingFaceH4/zephyr-7b-beta")
```

This allows you to more easily use any model on the Hugging Face hub in
[SafeTensors format](https://huggingface.co/docs/safetensors/index)
provided it can be loaded with `transformers.AutoModelForCausalLM` (or
`transformers.AutoModelForVision2Seq`). Note that, when using the
`model_id` parameter, the `prompt_template` is set automatically by
`transformers`.

Using the `transformers` backend requires the
[bitsandbytes](https://huggingface.co/docs/bitsandbytes/main/en/installation)
library, a lightweight Python wrapper around CUDA custom functions, in
particular 8-bit optimizers, matrix multiplication (LLM.int8()), and 8 &
4-bit quantization functions. There are ongoing efforts by the
bitsandbytes team to support multiple backends in addition to CUDA.
However, we have only tested with a CUDA backend (CUDA 12.x). If you
receive errors related to bitsandbytes, please refer to the
[bitsandbytes
documentation](https://huggingface.co/docs/bitsandbytes/main/en/installation).

### Connecting to LLMs Served Through REST APIs

**OnPrem.LLM** can be used with LLMs being served through any
OpenAI-compatible REST API. This means you can easily use **OnPrem.LLM**
with tools like [vLLM](https://github.com/vllm-project/vllm),
[OpenLLM](https://github.com/bentoml/OpenLLM),
[Ollama](https://ollama.com/blog/openai-compatibility), and the
[llama.cpp
server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md).

For instance, using [vLLM](https://github.com/vllm-project/vllm), you
can serve a LLaMA 3 model as follows:

``` sh
python -m vllm.entrypoints.openai.api_server --model NousResearch/Meta-Llama-3-8B-Instruct --dtype auto --api-key token-abc123
```

You can then connect OnPrem.LLM to the LLM by supplying the URL of the
server you just started:

``` python
from onprem import LLM
llm = LLM(model_url='http://localhost:8000/v1', api_key='token-abc123') 
# Note: The API key can either be supplied directly or stored in the OPENAI_API_KEY environment variable.
#       If the server does not require an API key, `api_key` should still be supplied with a dummy value like 'na'.
```

That’s it! Solve problems with **OnPrem.LLM** as you normally would
(e.g., RAG question-answering, summarization, few-shot prompting, code
generation, etc.).

### Using OpenAI Models with OnPrem.LLM

Even when using on-premises language models, it can sometimes be useful
to have easy access to non-local, cloud-based models (e.g., OpenAI) for
testing, producing baselines for comparison, and generating synthetic
examples for fine-tuning. For these reasons, in spite of the name,
**OnPrem.LLM** now includes support for OpenAI chat models:

``` python
from onprem import LLM
llm = LLM(model_url='openai://gpt-4o', temperature=0)
```

    /home/amaiya/projects/ghub/onprem/onprem/core.py:196: UserWarning: The model you supplied is gpt-4o, an external service (i.e., not on-premises). Use with caution, as your data and prompts will be sent externally.
      warnings.warn(f'The model you supplied is {self.model_name}, an external service (i.e., not on-premises). '+\

``` python
saved_result = llm.prompt('List three cute  names for a cat and explain why each is cute.')
```

    Certainly! Here are three cute names for a cat, along with explanations for why each is adorable:

    1. **Whiskers**: This name is cute because it highlights one of the most distinctive and charming features of a cat—their whiskers. It's playful and endearing, evoking the image of a curious cat twitching its whiskers as it explores its surroundings.

    2. **Mittens**: This name is cute because it conjures up the image of a cat with little white paws that look like they are wearing mittens. It's a cozy and affectionate name that suggests warmth and cuddliness, much like a pair of soft mittens.

    3. **Pumpkin**: This name is cute because it brings to mind the warm, orange hues of a pumpkin, which can be reminiscent of certain cat fur colors. It's also associated with the fall season, which is often linked to comfort and coziness. Plus, the name "Pumpkin" has a sweet and affectionate ring to it, making it perfect for a beloved pet.

``` python
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
saved_result = llm.prompt('Describe the weather in this image.', image_path_or_url=image_url)
```

    The weather in the image appears to be clear and sunny. The sky is mostly blue with some scattered clouds, suggesting a pleasant day with good visibility. The sunlight is bright, illuminating the green grass and landscape.

**Azure OpenAI**

For Azure OpenAI models, use the following URL format:

``` python
llm = LLM(model_url='azure://<deployment_name>', ...) 
# <deployment_name> is the Azure deployment name and additional Azure-specific parameters 
# can be supplied as extra arguments to LLM (or set as environment variables)
```

### Guided Prompts

You can use **OnPrem.LLM** with the
[Guidance](https://github.com/guidance-ai/guidance) package to guide the
LLM to generate outputs based on your conditions and constraints. We’ll
show a couple of examples here, but see [our documentation on guided
prompts](https://amaiya.github.io/onprem/examples_guided_prompts.html)
for more information.

``` python
from onprem import LLM

llm = LLM(n_gpu_layers=-1, verbose=False)
from onprem.guider import Guider
guider = Guider(llm)
```

With the Guider, you can use use Regular Expressions to control LLM
generation:

``` python
prompt = f"""Question: Luke has ten balls. He gives three to his brother. How many balls does he have left?
Answer: """ + gen(name='answer', regex='\d+')

guider.prompt(prompt, echo=False)
```

    {'answer': '7'}

``` python
prompt = '19, 18,' + gen(name='output', max_tokens=50, stop_regex='[^\d]7[^\d]')
guider.prompt(prompt)
```

<pre style='margin: 0px; padding: 0px; padding-left: 8px; margin-left: -8px; border-radius: 0px; border-left: 1px solid rgba(127, 127, 127, 0.2); white-space: pre-wrap; font-family: ColfaxAI, Arial; font-size: 15px; line-height: 23px;'>19, 18<span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>7</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>6</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>5</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>4</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>3</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>2</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 1</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>0</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 9</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'> 8</span><span style='background-color: rgba(0, 165, 0, 0.15); border-radius: 3px;' title='0.0'>,</span></pre>

    {'output': ' 17, 16, 15, 14, 13, 12, 11, 10, 9, 8,'}

See [the
documentation](https://amaiya.github.io/onprem/examples_guided_prompts.html)
for more examples of how to use
[Guidance](https://github.com/guidance-ai/guidance) with **OnPrem.LLM**.

## Built-In Web App

**OnPrem.LLM** includes a built-in Web app to access the LLM. To start
it, run the following command after installation:

``` shell
onprem --port 8000
```

Then, enter `localhost:8000` (or `<domain_name>:8000` if running on
remote server) in a Web browser to access the application:

<img src="https://raw.githubusercontent.com/amaiya/onprem/master/images/onprem_screenshot.png" border="1" alt="screenshot" width="775"/>

For more information, [see the corresponding
documentation](https://amaiya.github.io/onprem/webapp.html).

## Speeding Up Inference Using a GPU

The above example employed the use of a CPU. If you have a GPU (even an
older one with less VRAM), you can speed up responses. See [the
llama-cpp-python
documentation](https://llama-cpp-python.readthedocs.io/en/latest/#installation)
for installing `llama-cpp-python` with GPU support for your system.

The steps below describe installing and using `llama-cpp-python` with
`CUDA` support and can be employed for GPU acceleration on systems with
NVIDIA GPUs (e.g., Linux, WSL2, Google Colab).

#### Step 1: Install `llama-cpp-python` with GPU support

``` shell
CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir

# For Mac users replace above with:
# CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

#### Step 2: Use the `n_gpu_layers` argument with [`LLM`](https://amaiya.github.io/onprem/core.html#llm)

``` python
llm = LLM(n_gpu_layers=35)
```

The value for `n_gpu_layers` depends on your GPU memory and the model
you’re using (e.g., max of 33 for default 7B model). Set
`n_gpu_layers=-1` to offload all layers to the GPU (this will offload
all 33 layers to the default model). You can reduce the value if you get
an error (e.g., `CUDA error: out-of-memory`). For instance, using two
old NVDIDIA TITAN V GPUs each with 12GB of VRAM, 59 out 83 layers in a
[quantized Llama-2 70B
model](https://huggingface.co/TheBloke/Llama-2-70B-chat-GGUF/resolve/main/llama-2-70b-chat.Q3_K_S.gguf)
can be offloaded to the GPUs (i.e., 60 layers or more results in a “CUDA
out of memory” error).

With the steps above, calls to methods like `llm.prompt` will offload
computation to your GPU and speed up responses from the LLM.

The above assumes that NVIDIA drivers and the CUDA toolkit are already
installed. On Ubuntu Linux systems, this can be accomplished [with a
single
command](https://lambdalabs.com/lambda-stack-deep-learning-software).

## FAQ

1.  **How do I use other models with OnPrem.LLM?**

    > You can supply the URL to other models to the `LLM` constructor,
    > as we did above in the code generation example.

    > As of v0.0.20, we support models in GGUF format, which supersedes
    > the older GGML format. You can find llama.cpp-supported models
    > with `GGUF` in the file name on
    > [huggingface.co](https://huggingface.co/models?sort=trending&search=gguf).

    > Make sure you are pointing to the URL of the actual GGUF model
    > file, which is the “download” link on the model’s page. An example
    > for **Mistral-7B** is shown below:

    > <img src="https://raw.githubusercontent.com/amaiya/onprem/master/images/model_download_link.png" border="1" alt="screenshot" width="775"/>

    > Note that some models have specific prompt formats. For instance,
    > the prompt template required for **Zephyr-7B**, as described on
    > the [model’s
    > page](https://huggingface.co/TheBloke/zephyr-7B-beta-GGUF), is:
    >
    > `<|system|>\n</s>\n<|user|>\n{prompt}</s>\n<|assistant|>`
    >
    > So, to use the **Zephyr-7B** model, you must supply the
    > `prompt_template` argument to the `LLM` constructor (or specify it
    > in the `webapp.yml` configuration for the Web app).
    >
    > ``` python
    > # how to use Zephyr-7B with OnPrem.LLM
    > llm = LLM(model_url='https://huggingface.co/TheBloke/zephyr-7B-beta-GGUF/resolve/main/zephyr-7b-beta.Q4_K_M.gguf',
    >           prompt_template = "<|system|>\n</s>\n<|user|>\n{prompt}</s>\n<|assistant|>",
    >           n_gpu_layers=33)
    > llm.prompt("List three cute names for a cat.")
    > ```

2.  **When installing `onprem`, I’m getting “build” errors related to
    `llama-cpp-python` (or `chroma-hnswlib`) on Windows/Mac/Linux?**

    > See [this LangChain documentation on
    > LLama.cpp](https://python.langchain.com/docs/integrations/llms/llamacpp)
    > for help on installing the `llama-cpp-python` package for your
    > system. Additional tips for different operating systems are shown
    > below:

    > For **Linux** systems like Ubuntu, try this:
    > `sudo apt-get install build-essential g++ clang`. Other tips are
    > [here](https://github.com/oobabooga/text-generation-webui/issues/1534).

    > For **Windows** systems, please try following [these
    > instructions](https://github.com/amaiya/onprem/blob/master/MSWindows.md).
    > We recommend you use [Windows Subsystem for Linux
    > (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install)
    > instead of using Microsoft Windows directly. If you do need to use
    > Microsoft Window directly, be sure to install the [Microsoft C++
    > Build
    > Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
    > and make sure the **Desktop development with C++** is selected.

    > For **Macs**, try following [these
    > tips](https://github.com/imartinez/privateGPT/issues/445#issuecomment-1563333950).

    > There are also various other tips for each of the above OSes in
    > [this privateGPT repo
    > thread](https://github.com/imartinez/privateGPT/issues/445). Of
    > course, you can also [easily
    > use](https://colab.research.google.com/drive/1LVeacsQ9dmE1BVzwR3eTLukpeRIMmUqi?usp=sharing)
    > **OnPrem.LLM** on Google Colab.

    > Finally, if you still can’t overcome issues with building
    > `llama-cpp-python`, you can try [installing the pre-built wheel
    > file](https://abetlen.github.io/llama-cpp-python/whl/cpu/llama-cpp-python/)
    > for your system:

    > **Example:**
    > `pip install llama-cpp-python==0.2.90 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu`
    >
    > **Tip:** There are [pre-built wheel files for
    > `chroma-hnswlib`](https://pypi.org/project/chroma-hnswlib/#files),
    > as well. If running `pip install onprem` fails on building
    > `chroma-hnswlib`, it may be because a pre-built wheel doesn’t yet
    > exist for the version of Python you’re using (in which case you
    > can try downgrading Python).

3.  **I’m behind a corporate firewall and am receiving an SSL error when
    trying to download the model?**

    > Try this:
    >
    > ``` python
    > from onprem import LLM
    > LLM.download_model(url, ssl_verify=False)
    > ```

    > You can download the embedding model (used by `LLM.ingest` and
    > `LLM.ask`) as follows:
    >
    > ``` sh
    > wget --no-check-certificate https://public.ukp.informatik.tu-darmstadt.de/reimers/sentence-transformers/v0.2/all-MiniLM-L6-v2.zip
    > ```

    > Supply the unzipped folder name as the `embedding_model_name`
    > argument to `LLM`.

    > If you’re getting SSL errors when even running `pip install`, try
    > this:
    >
    > ``` sh
    > pip install –-trusted-host pypi.org –-trusted-host files.pythonhosted.org pip_system_certs
    > ```

4.  **How do I use this on a machine with no internet access?**

    > Use the `LLM.download_model` method to download the model files to
    > `<your_home_directory>/onprem_data` and transfer them to the same
    > location on the air-gapped machine.

    > For the `ingest` and `ask` methods, you will need to also download
    > and transfer the embedding model files:
    >
    > ``` python
    > from sentence_transformers import SentenceTransformer
    > model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    > model.save('/some/folder')
    > ```

    > Copy the `some/folder` folder to the air-gapped machine and supply
    > the path to `LLM` via the `embedding_model_name` parameter.

5.  **My model is not loading when I call `llm = LLM(...)`?**

    > This can happen if the model file is corrupt (in which case you
    > should delete from `<home directory>/onprem_data` and
    > re-download). It can also happen if the version of
    > `llama-cpp-python` needs to be upgraded to the latest.

6.  **I’m getting an `“Illegal instruction (core dumped)` error when
    instantiating a `langchain.llms.Llamacpp` or `onprem.LLM` object?**

    > Your CPU may not support instructions that `cmake` is using for
    > one reason or another (e.g., [due to Hyper-V in VirtualBox
    > settings](https://stackoverflow.com/questions/65780506/how-to-enable-avx-avx2-in-virtualbox-6-1-16-with-ubuntu-20-04-64bit)).
    > You can try turning them off when building and installing
    > `llama-cpp-python`:

    > ``` sh
    > # example
    > CMAKE_ARGS="-DGGML_CUDA=ON -DGGML_AVX2=OFF -DGGML_AVX=OFF -DGGML_F16C=OFF -DGGML_FMA=OFF" FORCE_CMAKE=1 pip install --force-reinstall llama-cpp-python --no-cache-dir
    > ```

7.  **How can I speed up
    [`LLM.ingest`](https://amaiya.github.io/onprem/core.html#llm.ingest)
    using my GPU?**

    > Try using the `embedding_model_kwargs` argument:
    >
    > ``` python
    > from onprem import LLM
    > llm  = LLM(embedding_model_kwargs={'device':'cuda'})
    > ```
