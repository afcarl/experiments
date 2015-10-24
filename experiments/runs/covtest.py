from __future__ import print_function, division, absolute_import

import shapely
import shapely.ops
import shapely.geometry

import toolbox
import learners
from learners import tools

from ..tools import chrono


def cov_test(cfg):

    ticks = set(cfg.test.ticks)
    history = chrono.ChronoHistory(cfg.hardware.datafile, core_keys=['errors'],
                                   meta={'jobcfg': cfg},
                                   extralog = False)

    sensory_data = chrono.ChronoHistory(cfg.hardware.exploration.sensoryfile,
                                        extralog = False, verbose=True)
    data_cfg = sensory_data.core.meta['jobcfg'].exploration

    points = []
    for tick, entry in enumerate(sensory_data):
        if tick in ticks:

            if len(history) <= tick or history.core.entries[tick] is None:
                history.add_entry(tick, {'errors': [shapely.ops.unary_union(points).area]}, delete_posterior=False)

        s_vector = tools.to_vector(entry['data']['s_signal'], data_cfg.explorer.s_channels)
        points.append(shapely.geometry.Point(s_vector).buffer(cfg.test.buffer_size))

    if len(sensory_data) in ticks:
        history.add_entry(len(sensory_data), {'errors': [shapely.ops.unary_union(points).area]}, delete_posterior=False)

    history.save(done=True, verbose=True)
