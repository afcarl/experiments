# versioneer
from ._version import get_versions
__version__ = get_versions()["version"]
__commit__ = get_versions()["full-revisionid"]
__dirty__ = get_versions()["dirty"]
del get_versions

__url__ = 'https://github.com/humm/experiments'


# intra-imports
from .expcfg import desc
from .execute import run_exps
from .runs.main import run_job

from .jobs.tests import testcov_cfg, testnn_cfg, testinv_cfg
from .jobs.keys import expkey

from .data.data import DataResults, DataExploration, DataSensoryExploration
from .data.data import load_explorations, load_results, load_exploration, load_result
