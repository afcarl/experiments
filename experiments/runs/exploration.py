
from __future__ import print_function, absolute_import
import random
import sys

from clusterjobs import datafile
import environments
import explorers
import learners

from ..tools import chrono


def exploration_step(env, explorer, tries=3):
    """Explore the step"""
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

def load_existing_datafile(cfg, core_keys):
    """Load existing datafile and checks, if it exists."""
    if datafile.isfile(cfg.hardware.datafile):
        history = chrono.ChronoHistory(cfg.hardware.datafile, cfg.hardware.logfile,
                                       core_keys=core_keys,
                                       extralog=cfg.hardware.logs,
                                       autosave_period=cfg.hardware.autosave_period,
                                       verbose=True)
        # compare config.run with config
        assert history.meta['jobcfg.pristine'] == cfg
        # load config.track & tracking checks
        #tracking.check(history.meta['cfg.track'])
        return history

def load_src_files(cfg, env_m_channels):
    """Load datafile from the source tasks and create corresponding datasets"""
    src_datasets = []

    for src_filepath in cfg.hardware.src_files:
        src_history      = chrono.ChronoHistory(src_filepath, extralog=False, verbose=True)
        src_explorations = [(entry['data']['exploration'], entry['data']['feedback'])  for entry in src_history]
        src_cfg          = src_history.meta['jobcfg']['exploration']
        src_dataset      = {'m_channels'  : src_cfg.explorer.m_channels,
                            's_channels'  : src_cfg.explorer.s_channels,
                            'explorations': src_explorations}
        src_datasets.append(src_dataset)
        assert env_m_channels == src_cfg.explorer.m_channels

    return src_datasets

def explore(cfg):
    cfg_orig = cfg._deepcopy()

    try:
            ## Load Potentially Existing Data ##
        history = load_existing_datafile(cfg, core_keys=('exploration', 'feedback'))
        if history is None:
            # set a random seed if none already set.
            cfg.hardware._setdefault('seed', random.randint(0, 9223372036854775807)) # sys.maxint
        else:
            # replace config by the previous (matching) config,
            # as it contains non-reproductible explorers uuids, and tracking data.
            cfg = history.meta['jobcfg.track']

        random.seed(cfg.hardware.seed)


            ## Instanciating the environment ##

        env = environments.Environment.create(cfg.exploration.env)


            ## Instanciating the explorer ##

        src_datasets = load_src_files(cfg, env.m_channels)
        if history is None:
            cfg.exploration.explorer.m_channels = env.m_channels
            cfg.exploration.explorer.s_channels = env.s_channels
        explorer = explorers.Explorer.create(cfg.exploration.explorer, datasets=src_datasets)
        print('configuration:\n', cfg, '\n', sep='')


            ## Running learning ##

        if history is None:
            history = chrono.ChronoHistory(cfg.hardware.datafile, cfg.hardware.logfile,
                                           meta={'jobcfg.pristine': cfg_orig,
                                                 'jobcfg': cfg,
                                                 'm_channels': env.m_channels,
                                                 's_channels': env.s_channels,
                                                 'random_state': random.getstate()},
                                           core_keys=('exploration', 'feedback'),
                                           extralog       =cfg.hardware.logs,
                                           autosave_period=cfg.hardware.autosave_period,
                                           verbose        =True)

        # setting random state
        random.setstate(history.meta['random_state'])

        # replaying history
        for entry in history:
            explorer.receive(entry['data']['exploration'], entry['data']['feedback'])
        history.enable_autosave()

        # class AutoSave(object):
        #
        #     def __init__(self, cfg):
        #         self.last_save = time.time()
        #         self.autosave_period = cfg.hardware.autosave_period
        #
        #     def autosave(self):
        #         if time.time() > self.autosave_period + self.last_save:
        #             self.last_save = time.time()
        #             return True
        #         return False

        # running exploration
        for t in range(len(history), cfg.exploration.steps):
            entry = exploration_step(env, explorer)
            history.add_entry(t, entry)
            # if autosave.autosave():
            #     # save history


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
        datafile.save_config(cfg, filename=cfg.hardware.configfile+'.done', directory='')

    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        env.close()
