from __future__ import print_function, division, absolute_import

from clusterjobs import datafile

import environments
import explorers
from environments import tools

from ..tools import chrono


def make_testset(cfg):

    meta = {}
    testset_history = chrono.ChronoHistory(cfg.hardware.datafile, core_keys=[''],
                                           meta=meta, extralog = False)

    # if cfg[stage].algorithm == 'random.sensory':
    #     env = environments.Environment.create(cfg.job.env)
    #
    #     meta['testset'] = tuple(tools.random_signal(env.s_channels) for _ in range(cfg[stage].size))
    #     meta['s_channels'] = env.s_channels
    #
    # # if cfg[stage].algorithm == 'isogrid.sensory':
    # #     env = environments.Environment.create(cfg.job.env)
    #
    # #     cfg[stage].res = []
    #
    # #     for cfg[stage].
    # #     meta['testset'] = tuple(tools.random_signal(env.s_channels) for _ in range(cfg[stage].size))
    # #     meta['s_channels'] = env.s_channels
    #
    # elif cfg[stage].algorithm == 'uniform.sensory':
    #
    #     meshgrid = None
    #     # create meshgrid
    #
    #     for filename in cfg.hardware.datafiles:
    #
    #         data = chrono.ChronoHistory(filename, extralog=False, verbose=True)
    #
    #         if meshgrid is None:
    #             s_channels = data.core.meta['s_channels']
    #             meshgrid = explorers.MeshGrid([c.bounds for c in s_channels], cfg[stage].res)
    #
    #         for entry in data:
    #             # populate meshgrid
    #             s_signal = entry['data']['feedback']['s_signal']
    #             s_vector = tools.to_vector(s_signal, s_channels)
    #             meshgrid.add(s_vector)
    #
    #     # draw from meshgrid
    #     testset = []
    #     for _ in range(cfg[stage].size):
    #         s_vector = meshgrid.draw(replace=False)
    #         s_signal = tools.to_signal(s_vector, s_channels)
    #         testset.append(s_signal)
    #
    #     meta['testset']    = testset
    #     meta['s_channels'] = s_channels

    if cfg.testset.algorithm == 'fromfile': # the set is provided

        dataset = datafile.load_file(cfg.testset.input_file)

        meta['testset']    = dataset['s_signals']
        meta['s_channels'] = dataset['s_channels']

    else:
        raise NotImplementedError('unknown testset creation method')

    testset_history.save(done=True, verbose=True)
