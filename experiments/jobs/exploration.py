import os
import numbers
import collections

import scicfg

from . import basejobs
from .keys import JobKey, expkey
from ..expcfg import hardware_cfg


exp_desc_cfg = scicfg.SciConfig(strict=True)
exp_desc_cfg._branch('exploration.explorer', strict=False)
exp_desc_cfg._branch('exploration.env', strict=False)
exp_desc_cfg._describe('exploration.ex_name', instanceof=str, docstring='the name of the explorer')
exp_desc_cfg._describe('exploration.env_name', instanceof=str, docstring='the name of the environment')
exp_desc_cfg._describe('exploration.steps', instanceof=numbers.Integral, docstring='the number of trials')
exp_desc_cfg._describe('exploration.seeds', instanceof=collections.Iterable, docstring='random seeds')

job_desc_cfg = scicfg.SciConfig(strict=True)
job_desc_cfg._describe('key', instanceof=collections.Iterable, docstring='unique key for the job')
job_desc_cfg._describe('rep', instanceof=numbers.Integral, docstring='job repetition number')
#job_desc_cfg._describe('key', instanceof=numbers.Integer, docstring='repetition number')
job_desc_cfg._describe('name', instanceof=str, docstring='unique name for the job')
job_desc_cfg._branch('exploration', value=exp_desc_cfg.exploration._deepcopy())
# del job_desc_cfg.exploration.seeds

ex_hardware_cfg = hardware_cfg._deepcopy()
ex_hardware_cfg._describe('sensoryfile', instanceof=str, docstring='contains only effects (no motor command)')
ex_hardware_cfg._describe('src_files', instanceof=collections.Iterable, docstring='files of reused datasets')
job_desc_cfg._branch('hardware', value=ex_hardware_cfg._deepcopy())

job_desc_cfg._branch('provenance', strict=False)

class ExplorationJob(basejobs.ConfigJob):

    def make_jobcfg(self, expcfg, rep):
        self.jobkey = JobKey(('exploration',), expkey(expcfg), rep)

        self.jobcfg = job_desc_cfg._deepcopy()
        self.jobcfg.key  = self.jobkey.key
        self.jobcfg.rep  = self.jobkey.rep
        self.jobcfg.name = self.jobkey.name

        for k in ['ex_name', 'explorer', 'env_name', 'env', 'steps', 'deps']:
            self.jobcfg.exploration[k] = expcfg.exploration[k]

        self.jobcfg.hardware.configfile  = self.jobkey.filepath + '.cfg'
        self.jobcfg.hardware.datafile    = self.jobkey.filepath + '.d'
        self.jobcfg.hardware.sensoryfile = self.jobkey.filepath + '.ds'
        self.jobcfg.hardware.logfile     = self.jobkey.filepath + '.log'
        self.jobcfg.hardware.seed        = expcfg.exploration.seeds[rep]

    def prepare(self, args):
        expcfg, rep = args
        self.make_jobcfg(expcfg, rep)

        self.add_input_file(self.jobcfg.hardware.configfile,        full=True)
        self.add_output_file(self.jobcfg.hardware.sensoryfile,      full=True)
        self.add_output_file(self.jobcfg.hardware.datafile,         full=True)
        self.add_output_file(self.jobcfg.hardware.datafile+'.done', full=True)

        self._finalize()

        self.jobcfg.hardware.src_files = []
        for expkeydep in self.jobcfg.exploration.deps:
            jobkeydep = JobKey(('exploration',), expkeydep, self.jobcfg.rep)
            jobdep = self.jobgroup.jobs_byname[jobkeydep.name]
            rel_path = os.path.relpath(jobdep.context.fullpath(''), self.context.fullpath(''))
            src_filepath = os.path.join(rel_path, jobdep.jobcfg.hardware.datafile)
            self.jobcfg.hardware.src_files.append(src_filepath)

            self.add_input_file(src_filepath,         full=True)
            self.add_input_file(src_filepath+'.done', full=True)
