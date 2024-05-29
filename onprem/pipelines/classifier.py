# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/04_pipelines.classifier.ipynb.

# %% auto 0
__all__ = ['DEFAULT_SETFIT_MODEL', 'SMALL_SETFIT_MODEL', 'DATASET_TEXT', 'DATASET_LABEL', 'ClassifierBase', 'FewShotClassifier']

# %% ../../nbs/04_pipelines.classifier.ipynb 3
import os
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, Callable
from setfit import SetFitModel, TrainingArguments, Trainer, sample_dataset, SetFitTrainer

# %% ../../nbs/04_pipelines.classifier.ipynb 4
import warnings
from abc import ABC, abstractmethod
DEFAULT_SETFIT_MODEL = "sentence-transformers/paraphrase-mpnet-base-v2"
SMALL_SETFIT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DATASET_TEXT = "text"
DATASET_LABEL = "label"

class ClassifierBase(ABC):

  
    @abstractmethod
    def train(self,
              X:List[str],
              y:Union[List[int], List[str]],
              max_steps:int=50,
              num_epochs:int=10,
              batch_size:int=32,
              **kwargs,
             ):
        """
        Trains the classifier on a list of texts (`X`) and a list of labels (`y`).
        Additional keyword arguments are passed directly to `SetFit.TrainingArguments`.

        **Args:**

        - *X*: List of texts
        - *y*: List of integers representing labels
        - *max_steps*: If set to a positive number, the total number of training steps to perform. Overrides num_epochs. 
        - *num_epochs*: Number of epochs to train
        - *batch_size*: Batch size

        **Returns:**

        - None
        """
        pass

    @abstractmethod
    def save(self, save_path:str):
        """
        Save model to specified folder path, `save_path`
        """
        pass


    def sample_examples(self, X:list, y:list, num_samples:int=8,
                        text_key:str=DATASET_TEXT, label_key:str=DATASET_LABEL):
        """
        Sample a dataset with `num_samples` per class
        """
        full_dataset = self.arrays2dataset(X, y, text_key=text_key, label_key=label_key)
                
        sample = sample_dataset(full_dataset, label_column=label_key, num_samples=num_samples)
        return sample.to_dict()[text_key], sample.to_dict()[label_key]
        

    
    def arrays2dataset(self, X:List[str], y:Union[List[int], List[str]], 
                       text_key:str=DATASET_TEXT, label_key:str=DATASET_LABEL):
        """
        Convert train or test examples to HF dataset
        """
        from datasets import Dataset
        return Dataset.from_dict({text_key:X, label_key:y})


    def dataset2arrays(self, dataset, text_key:str=DATASET_TEXT, label_key:str=DATASET_LABEL):
        """
        Convert a Hugging Face dataset to X, y arrays
        """
        return dataset.to_dict()['text'], dataset.to_dict()['label']
        
    def get_trainer(self):
        """
        Retrieves last trainer
        """
        if not self.trainer:
            raise ValueError('A trainer has not been created yet. You must first train a model on some labeled examples ' +\
                             'using the FewShotClassifier.train method.')
        return self.trainer

    
    def evaluate(self, X_eval:list, y_eval:list, print_report:bool=False, labels:List[str]=[]):
        """
        Evaluates labeled data using the trained model. 
        If `print_report` is True, prints classification report and returns nothing.
        Otherwise, returns and prints a dictionary of the results.

        
        """
        from sklearn.metrics import classification_report
        y_pred= self.predict(X_eval)
        if self.model.labels:
            y_pred = [self.model.labels.index(y) for y in y_pred]
            if y_eval[0] in self.model.labels:
                y_eval = [self.model.labels.index(y) for y in y_eval]

        result = classification_report(y_eval, y_pred, 
                                       output_dict=not print_report, 
                                       target_names= self.get_labels(labels))
        if print_report:
            return result
        else:
            import yaml
            print(yaml.dump(result, allow_unicode=True, default_flow_style=False))
            return result



    def explain(self, X:list, labels:List[str]=[]):
        """
        Explain the predictions on given examples in `X`. (Requires `shap` and `matplotlib` to be installed.)
        """
        try:
            import shap
        except ImportError:
            raise ImportError('Please install the shap library: pip install shap')

        try:
            import matplotlib
        except ImportError:
            raise ImportError('Please install the matplotlib library: pip install matplotlib')

        def f(x):
            return self.predict_proba(x)
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.model_id_or_path)

        
        output_names = self.get_labels(labels)
        explainer = shap.Explainer(f, tokenizer, output_names=self.get_labels(labels))
        shap_values = explainer(X)
        shap.plots.text(shap_values)
          
    def get_labels(self, labels:List[str]=[]):
        """
        Inspect model and return labels
        """
        target_names = labels if labels else self.model.labels
        target_names = target_names if target_names else None
        return target_names

class FewShotClassifier(ClassifierBase):
    def __init__(
        self,
        model_id_or_path:str=DEFAULT_SETFIT_MODEL,
        use_smaller:bool=False,
        **kwargs,
    ):
        """
        `FewShotClassifier` can be used to train and run text classifiers. Currently based on SetFit.
                Additional keyword arguments are fed directly to `from_pretrained`.


        **Args:**

        - *model_id_or_path*: The Hugging Face model_id or path to model folder (e.g, path previously trained and saved model).
        - *use_smaller*:  If True, will use a smaller but performant model.

        """
        self.model_id_or_path = model_id_or_path
        if use_smaller and model_id_or_path != DEFAULT_SETFIT_MODEL:
            warnings.warn(f'Over-writing supplied model ({model_id_or_path}) with {SMALL_MODEL} because use_smaller=True.')
        self.model_id_or_path = SMALL_SETFIT_MODEL if use_smaller else self.model_id_or_path
        self.model = SetFitModel.from_pretrained(self.model_id_or_path, **kwargs)
        self.predict = self.model.predict
        self.predict_proba = self.model.predict_proba
        self.trainer = None # set in `FewShotClassifier.train`
        self.labels = [] # set in `FewShotClassifier.train`
         
        
    def train(self,
              X:List[str],
              y:Union[List[int], List[str]],
              num_epochs:int=10,
              batch_size:int=32,
              **kwargs,
             ):
        """
        Trains the classifier on a list of texts (`X`) and a list of labels (`y`).
        Additional keyword arguments are passed directly to `SetFit.TrainingArguments`.

        **Args:**

        - *X*: List of texts
        - *y*: List of integers representing labels
        - *num_epochs*: Number of epochs to train
        - *batch_size*: Batch size

        **Returns:**

        - None
        """

        # convert to HF dataset
        train_dataset = self.arrays2dataset(X, y, text_key='text', label_key='label')

        args = TrainingArguments(
                batch_size=batch_size,
                num_epochs=num_epochs,
                **kwargs
        )      

        trainer = Trainer(
                    model=self.model,
                    args=args,
                    train_dataset=train_dataset,
                    column_mapping={"text": "text", "label": "label"}
        )
        trainer.train()

        # DEPRECATED
        # trainer = SetFitTrainer(model=self.model, train_dataset=train_dataset)
        # trainer.train(batch_size=batch_size, num_epochs=num_epochs, **kwargs)
      
        self.trainer = trainer
  

    def save(self, save_path:str):
        """
        Save model to specified folder path, `save_path`
        """
        self.model.save_pretrained(save_path)        