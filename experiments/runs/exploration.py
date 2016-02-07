
from __future__ import print_function, absolute_import
import random
import sys

import scicfg
from clusterjobs import datafile
import environments
import explorers
import learners

from ..tools import chrono, autosave
from .. import provenance


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

def same_cfg(cfg_a, cfg_b):
    try:
        for key_a, v_a in cfg_a._items():
            assert cfg_b[key_a] == v_a
        for key_b, v_b in cfg_b._items():
            assert cfg_a[key_b] == v_b
        return True
    except (KeyError, AssertionError) as e:
        return False

def load_existing_datafile(cfg, core_keys):
    """Load existing datafile and checks, if it exists."""
    if datafile.isfile(cfg.hardware.datafile):
        history = chrono.ChronoHistory(cfg.hardware.datafile, cfg.hardware.logfile,
                                       core_keys=core_keys,
                                       extralog=cfg.hardware.logs,
                                       verbose=True)
        # compare config.run with config
        if not same_cfg(history.meta['jobcfg.pristine'], cfg): # if not the same, restart from scratch
            print("configuration file does not match recorded configuration, restarting...")
            return None

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

def filter_entry(cfg, entry):
    """Filter meta info for inclusion in data files"""
    f_entry = {'exploration': entry['exploration'], 'feedback': entry['feedback'], 'meta': {}}
    for key in cfg.hardware.metadata:
        try:
            v = entry['meta']
            for k in key:
                v = v[k]
            f_entry['meta']['.'.join(key)] = v
        except KeyError:
            pass
    return f_entry


def explore(cfg):
    cfg_orig = cfg._deepcopy()
    autosave.period = cfg.hardware.autosave_period

    try:
            ## Load potentially existing data ##
        history = load_existing_datafile(cfg, core_keys=('exploration', 'feedback'))
        if history is None:
            # set a random seed if none already set.
            cfg.hardware._setdefault('seed', random.randint(0, 9223372036854775807)) # sys.maxint
        else:
            # replace config by the previous (matching) config,
            # as it contains non-reproductible explorers uuids, and provenance data.
            cfg = history.meta['jobcfg']

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

        prov_cfg = provenance.gather_provenance(cfg, env)

        if history is not None:
            try:
                provenance.check_provenance(cfg, prov_cfg)
            except AssertionError: # provenance changed: restarting from scratch
                print("continuity broken, restarting...")
                history = None

        if history is None:
            cfg.provenance._update(prov_cfg, overwrite=True)

            history = chrono.ChronoHistory(cfg.hardware.datafile, cfg.hardware.logfile,
                                           meta={'jobcfg.pristine': cfg_orig,
                                                 'jobcfg': cfg,
                                                 'm_channels': env.m_channels,
                                                 's_channels': env.s_channels,
                                                 'random_state': random.getstate()},
                                           core_keys=('exploration', 'feedback', 'meta'),
                                           extralog=cfg.hardware.logs,
                                           verbose=True, load=False)

        # replaying history
        for entry in history:
            explorer.receive(entry['data']['exploration'], entry['data']['feedback'])

        # setting random state
        random.setstate(history.meta['random_state'])

        # running exploration; the next three lines are the core of the experiment.
        for t in range(len(history), cfg.exploration.steps):
            entry = exploration_step(env, explorer)
            entry = filter_entry(cfg, entry)
            history.add_entry(t, entry)
            print('step {} done'.format(t))
            if autosave.autosave():
                # save history at regular intervals
                history.meta['random_state'] = random.getstate()
                history.save()
                print('autosaved...')


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

        history.meta['random_state'] = random.getstate()
        history.save(verbose=True, done=True)
        datafile.save_config(cfg, filename=cfg.hardware.configfile+'.done', directory='')

    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        env.close()
