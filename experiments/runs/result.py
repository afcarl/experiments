from __future__ import absolute_import, division, print_function

import numpy as np

import toolbox
import explorers

from ..tools import chrono


def astd(xs):
    m = np.average(xs)
    plus  = [x-m for x in xs if x >= m]
    minus = [x-m for x in xs if x <= m]
    sigma_plus  = np.std([-1*x for x in plus] + plus)
    sigma_minus = np.std([-1*x for x in minus] + minus)
    return (sigma_minus, sigma_plus)

def quantiles(xs):
    return np.percentile(xs, 100.0/4), np.percentile(xs, 3*100.0/4)



def compile_results(cfg):

    results = chrono.ChronoHistory(cfg.hardware.datafile, core_keys=['error_avgs', 'error_stds', 'avg', 'std'],
                                   extralog = False)

    for i, filename in enumerate(cfg.hardware.testfiles):
        test_history = chrono.ChronoHistory(filename, extralog=False, verbose=True)

        for tick, entry in enumerate(test_history):
            print(tick, entry)
            if entry is not None:
                results.setdefault(tick, {'error_avgs': [], 'error_stds': [],
                                          'avg': None, 'std': None})

                print(len(results.core.entries[tick]['data']['error_avgs']), i)
                print(results.core.entries[tick]['data']['error_avgs'])

                if 'errors' in entry['data']:
                    errors = entry['data']['errors']
                else:
                    assert False
                    errors = []
                    s_channels = entry['data']['testset']['s_channels']
                    for s_goal, feedback in zip(entry['data']['testset']['s_goals'], entry['data']['tests']):
                        s_v_test   = explorers.tools.to_vector(s_goal, s_channels)
                        s_v_actual = explorers.tools.to_vector(feedback['s_signal'], s_channels)
                        errors.append(toolbox.dist(s_v_test, s_v_actual))

                print(len(results.core.entries[tick]['data']['error_avgs']), i)
                assert len(results.core.entries[tick]['data']['error_avgs']) == i
                results.core.entries[tick]['data']['error_avgs'].append(np.average(errors))
                results.core.entries[tick]['data']['error_stds'].append(np.std(errors))

        test_history.close()

    for t, entry in enumerate(results.core.entries):
        if entry is not None:
            entry['data']['avg']      = np.average(entry['data']['error_avgs'])
            entry['data']['std']      = np.std(entry['data']['error_avgs'])

    results.save(verbose=True)

def run():
    from . import run_task
    run_task.run_task(compile_results)
