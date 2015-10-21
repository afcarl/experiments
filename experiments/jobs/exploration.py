import numbers
import collections

import forest

from . import basejobs
from ..expcfg import hardware_cfg


exp_desc_cfg = forest.Tree(strict=True)
exp_desc_cfg._branch('exploration.explorer', strict=False)
exp_desc_cfg._branch('exploration.env', strict=False)
exp_desc_cfg._describe('exploration.ex_name', instanceof=str, docstring='the name of the explorer')
exp_desc_cfg._describe('exploration.env_name', instanceof=str, docstring='the name of the environment')
exp_desc_cfg._describe('exploration.steps', instanceof=numbers.Integral, docstring='the number of trials')
exp_desc_cfg._describe('exploration.seeds', instanceof=collections.Iterable, docstring='random seeds')

job_desc_cfg = forest.Tree(strict=True)
job_desc_cfg._describe('key', instanceof=collections.Iterable, docstring='unique key for the job')
#job_desc_cfg._describe('key', instanceof=numbers.Integer, docstring='repetition number')
job_desc_cfg._describe('name', instanceof=str, docstring='unique name for the job')
job_desc_cfg._branch('exploration', value=exp_desc_cfg.exploration._deepcopy())
# del job_desc_cfg.exploration.seeds
job_desc_cfg._branch('hardware', value=hardware_cfg._deepcopy())
job_desc_cfg.hardware._describe('sensoryfile', instanceof=str, docstring='contains only effects (no motor command)')


class ExplorationJob(basejobs.ConfigJob):

    @classmethod
    def make_jobcfg(cls, expcfg, rep):
        jobkey = basejobs.JobKey(('exploration',), basejobs.expkey(expcfg), rep)

        jobcfg = job_desc_cfg._deepcopy()
        jobcfg.key  = jobkey.key
        jobcfg.name = jobkey.name

        for k in ['ex_name', 'explorer', 'env_name', 'env', 'steps']:
            jobcfg.exploration[k] = expcfg.exploration[k]

        jobcfg.hardware.configfile  = jobkey.filepath + '.cfg'
        jobcfg.hardware.datafile    = jobkey.filepath + '.d'
        jobcfg.hardware.sensoryfile = jobkey.filepath + '.fd'
        jobcfg.hardware.logfile     = jobkey.filepath + '.log'
        jobcfg.hardware.seed        = expcfg.exploration.seeds[rep]

        return jobcfg

    def prepare(self, args):
        expcfg, rep = args
        self.jobcfg = self.make_jobcfg(expcfg, rep)
        self.rep = rep

        self.add_input_file(self.jobcfg.hardware.configfile,        full=True)
        self.add_output_file(self.jobcfg.hardware.sensoryfile,      full=True)
        self.add_output_file(self.jobcfg.hardware.datafile,         full=True)
        self.add_output_file(self.jobcfg.hardware.datafile+'.done', full=True)

        self._finalize()

        # self.cfg['exploration.hardware.src_files'] = []
        # stage, key, depkeys = self.key
        # for src_key in depkeys:
        #     src_folder   = filenames.foldername(('exploration', src_key, ()))
        #     src_name     = filenames.filename(('exploration', src_key, ()))
        #     src_filepath = self.context.relpath(os.path.join(src_folder, src_name))
        #     self.cfg.exploration.hardware.src_files.append(src_filepath)
        #     self.add_input_file(src_filepath)
        #     self.add_input_file(src_filepath+'.done')
