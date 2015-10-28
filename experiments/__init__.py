from .expcfg import desc
from .execute import run_exps
from .runs.main import run_job

from .jobs.tests import testcov_cfg, testnn_cfg, testinv_cfg
from .jobs.keys import expkey

from .data.data import DataResults, DataExploration, DataSensoryExploration, load_explorations, load_results
