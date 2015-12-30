from __future__ import print_function, division, absolute_import

import learners
from learners import tools

from .. import tools
from ..tools import chrono


def measure_perf(tick, testset, nnset, data_cfg, history, light=False):
    errors = []
    for s_goal in testset['s_goals']:
        s_vector_goal = tools.to_vector(s_goal, testset['s_channels'])
        dist, idx = nnset.nn_y(s_vector_goal, k=1)
        s_vector = nnset.ys[idx[0]]
        errors.append(tools.dist(s_vector_goal, s_vector))

    print('log: test(t={}) done'.format(tick))

    history.add_entry(tick, {'errors': errors},
                      delete_posterior=False)

def nn_test(cfg):

        ## Loading exploration data ##

    data_history = chrono.ChronoHistory(cfg.hardware.exploration.datafile,
                                        extralog=False, verbose=True)
    data_cfg = data_history.core.meta['jobcfg'].exploration

    testset_chr = chrono.ChronoHistory(cfg.hardware.testset.datafile,
                                       extralog=False, verbose=True)
    testset = {'s_channels': testset_chr.core.meta['s_channels'],
               's_goals'   : testset_chr.core.meta['testset']}

    history = chrono.ChronoHistory(cfg.hardware.datafile, core_keys=['errors'],
                                   meta={'jobcfg': cfg, 'testset': testset},
                                   extralog = False)


    ticks = set(cfg.test.ticks)

    nnset = learners.NNSet()

    for tick, entry in enumerate(data_history):
        if tick in ticks and len(nnset) > 0:
            if len(history) <= tick or history.core.entries[tick] is None:
                measure_perf(tick, testset, nnset, data_cfg, history)

        exploration = entry['data']['exploration']
        feedback    = entry['data']['feedback']
        m_vector = tools.to_vector(exploration['m_signal'], data_cfg.explorer.m_channels)
        s_vector = tools.to_vector(   feedback['s_signal'], data_cfg.explorer.s_channels)
        nnset.add(m_vector, s_vector)

    if len(data_history) in ticks:
        measure_perf(len(data_history), testset, nnset, data_cfg, history)


    history.save(done=True, verbose=True)


def run():
    from . import run_task
    run_task.run_task(run_nn)
