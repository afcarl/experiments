import sys

from clusterjobs import datafile

from . import exploration

def run_job():
    cfg_filename = sys.argv[1]
    cfg = datafile.load_config(cfg_filename, verbose=True)

    if cfg.key[0] == ('exploration',):
        exploration.explore(cfg)
