import logging
import os

import torch
from farm.modeling.prediction_head import QuestionAnsweringHead

from model_pipeline.config_farm_train import Config

_logger = logging.getLogger(__name__)

# E.g. bert-base-uncased, roberta-base, roberta-large, albert-base-v2, albert-large-v2
# or any hugging face model e.g. deepset/roberta-base-squad2, a-ware/roberta-large-squadv2
# Full list at huggingface.co/models
base_LM_model = "a-ware/roberta-large-squadv2"


class QAConfig(Config):
    def __init__(self, project_name, output_model_name=None):
        super().__init__(experiment_type="KPI_EXTRACTION", project_name=project_name, output_model_name=output_model_name)


class QAFileConfig(QAConfig):

    def __init__(self, project_name, output_model_name):
        super().__init__(project_name, output_model_name)
        self.data_dir = os.path.join(self.root, "data")
        self.curated_data = os.path.join(self.data_dir, project_name, "interim", "ml", "training", "kpi_train.json")
        # If True, curated data will be split by dev_split ratio to train and val and saved in train_filename,
        # dev_filename . Otherwise train and val data will be loaded from mentioned filenames.
        self.perform_splitting = True #was False initially
        self.dev_split = .2
        self.train_filename = os.path.join(self.data_dir, project_name, "interim","ml", "training", "kpi_train_split.json")
        self.dev_filename = os.path.join(self.data_dir, project_name, "interim","ml","training", "kpi_val_split.json")
        self.test_filename = None
        self.saved_models_dir = os.path.join(self.root, "models", project_name, self.experiment_type, self.data_type, self.output_model_name)
        self.annotation_dir = os.path.join(self.data_dir, self.experiment_name, "interim", "ml", "annotations")
        self.training_dir = os.path.join(self.data_dir, self.experiment_name, "interim", "ml",  "training")


class QATokenizerConfig(QAConfig):

    def __init__(self, project_name):
        super().__init__(project_name)
        self.pretrained_model_name_or_path = base_LM_model
        self.do_lower_case = False


class QAProcessorConfig(QAConfig):

    def __init__(self, project_name):
        super().__init__(project_name)
        self.processor_name = "SquadProcessor"
        self.max_seq_len = 384
        self.label_list = ["start_token", "end_token"]
        self.metric = "squad"


class QAModelConfig(QAConfig):

    def __init__(self, project_name):
        super().__init__(project_name)
        self.class_type = QuestionAnsweringHead
        self.head_config = {}

        # set to None if you don't want to load the config file for this model
        self.load_dir = None #TODO: Should this really be None ?
        self.lang_model = base_LM_model
        self.layer_dims = [768, 2]
        self.lm_output_types = ["per_token"]


class QATrainingConfig(QAConfig):

    def __init__(self, project_name, seed):
        super().__init__(project_name)
        self.seed = seed
        self.run_hyp_tuning = False
        self.use_cuda = True

        # Check if GPU exists
        if not torch.cuda.is_available():
            _logger.warning("No gpu available, setting use_cuda to False")
            self.use_cuda = False

        self.use_amp = True
        self.distributed = False
        self.learning_rate = 2e-5
        self.n_epochs = 5
        self.evaluate_every = 50
        self.dropout = 0.1
        self.batch_size = 1
        self.grad_acc_steps = 8
        self.run_cv = False  # running cross-validation won't save a model
        if self.run_cv:
            self.evaluate_every = 0
        self.xval_folds = 5


class QAMLFlowConfig(QAConfig):

    def __init__(self, project_name):
        super().__init__(project_name)
        self.track_experiment = False
        self.run_name = self.experiment_name
        self.url = "http://localhost:5000"


class QAInferConfig(QAConfig):

    def __init__(self, project_name, output_model_name):
        super().__init__(project_name, output_model_name)
        # please change the following accordingly
        self.data_types = ["Text"]
        self.skip_processed_files = False  # If set to True, will skip inferring on already processed files
        self.top_k = 4
        self.result_dir = {"Text": os.path.join(self.root, "data", project_name, "output", self.experiment_type, "ml", "Text")}
        # Parameters for text inference
        self.load_dir = {"Text": os.path.join(self.root, "models", project_name, self.experiment_type, "Text", self.output_model_name)}
        self.batch_size = 16
        self.gpu = True
        # Set to value 1 (or 0) to disable multiprocessing. Set to None to let Inferencer use all CPU cores minus one.
        self.num_processes = None
        self.no_ans_boost = -15 # If increased, this will boost "No Answer" as prediction.
        # use large negative values (like -100) to disable giving "No answer" option.
