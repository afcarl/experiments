
from __future__ import print_function, absolute_import
import random
import sys

import environments
import explorers
import learners

from ..tools import chrono


def exploration_step(env, explorer, tries=3):
    try_count = 0
    while try_count < tries:
        try:
            meta = {}
            exploration = explorer.explore()

            m_signal = exploration['m_signal']
            feedback = env.execute(m_signal, meta=meta)
            break
        except env.OrderNotExecutableError:
            try_count += 1

    explorer.receive(exploration, feedback)
    return {'exploration': exploration, 'feedback': feedback, 'meta': meta}


def explore(cfg):

    try:
        # set a random seed
        cfg.hardware._setdefault('seed', random.randint(0, 9223372036854775807)) # sys.maxint
        random.seed(cfg.hardware.seed)


            ## Sources History ##
        src_m_channels = None
        src_datasets = []
        # for src_filepath in cfg.hardware.src_files:
        #     src_history = chrono.ChronoHistory(src_filepath,
        #                                        extralog=False, verbose=True)
        #     src_explorations = [(entry['data']['exploration'], entry['data']['feedback'])  for entry in src_history]
        #     src_cfg          = src_history.meta['jobcfg']['exploration']
        #     src_dataset  = {'m_channels'  : src_cfg.explorer.m_channels,
        #                     's_channels'  : src_cfg.explorer.s_channels,
        #                     'explorations': src_explorations}
        #     src_datasets.append(src_dataset)
        #
        #     assert src_m_channels is None or src_m_channels == src_cfg.explorer.m_channels
        #     src_m_channels = src_cfg.explorer.m_channels
        #

            ## Instanciation of core modules ##

        env = environments.Environment.create(cfg.exploration.env)
        assert len(src_datasets) == 0 or all(channels ==  env.m_channels for channels in src_m_channels), 'expected {}, got {}'.format(src_m_channels, env.m_channels)

        # to keep explorer uuid continuity
        existing_history = chrono.ChronoHistory(cfg.hardware.datafile, verbose=False)
        if existing_history.meta is not None:
            existing_cfg = existing_history.meta['jobcfg']
            cfg.exploration.explorer = existing_cfg.exploration.explorer
            cfg.exploration.explorer._freeze(False)

        cfg.exploration.explorer.m_channels = env.m_channels
        cfg.exploration.explorer.s_channels = env.s_channels
        explorer = explorers.Explorer.create(cfg.exploration.explorer, datasets=src_datasets)

        cfg._freeze(True)
        print('configuration:\n', cfg, '\n', sep='')


            ## Running learning ##

        history = chrono.ChronoHistory(cfg.hardware.datafile, cfg.hardware.logfile,
                                       meta={'jobcfg': cfg,
                                             'm_channels': env.m_channels,
                                             's_channels': env.s_channels},
                                       core_keys=('exploration', 'feedback'),
                                       extralog       =cfg.hardware.logs,
                                       autosave_period=cfg.hardware.autosave_period,
                                       verbose        =True)

        if len(history) > 0: # HACK, non-reproductible results if reloading existing data (i.e. after crash)
            random.seed()

        # replaying history
        for entry in history:
            explorer.receive(entry['data']['exploration'], entry['data']['feedback'])
        history.enable_autosave()

        # setting random state


        # running exploration
        for t in range(len(history), cfg.exploration.steps):
            entry = exploration_step(env, explorer)
            history.add_entry(t, entry)


            ## Finishing ##

        feedback_history = chrono.ChronoHistory(cfg.hardware.sensoryfile, None,
                                                core_keys=('s_signal', 'from'), load=False,
                                                meta={'jobcfg': cfg,
                                                      'm_channels': env.m_channels,
                                                      's_channels': env.s_channels})
        for t, entry in enumerate(history):
            exploration = entry['data']['exploration']
            feedback    = entry['data']['feedback']

            feedback_history.add_entry(t, {'s_signal': feedback['s_signal'], 'from': exploration['from']})
        feedback_history.save()

        history.save(verbose=True, done=True)

    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        env.close()
