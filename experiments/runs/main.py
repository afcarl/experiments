import sys

from clusterjobs import datafile

from . import exploration
from . import covtest
from . import nntest
from . import testset

def run_job():
    cfg_filename = sys.argv[1]
    cfg = datafile.load_config(cfg_filename, verbose=True)

    kind = cfg.key[0][0]
    if kind == 'exploration':
        exploration.explore(cfg)

    if kind == 'test':
        if cfg.test.kind == 'cov':
            covtest.cov_test(cfg)
        elif cfg.test.kind == 'nn':
            nntest.nn_test(cfg)

    if kind == 'testset':
        testset.make_testset(cfg)
