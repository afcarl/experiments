import numbers
import collections
import random

import forest

from . import basejobs
from .keys import JobKey, expkey
from ..expcfg import hardware_cfg


job_desc_cfg = forest.Tree(strict=True)
job_desc_cfg._describe('key', instanceof=collections.Iterable, docstring='unique key for the job')
job_desc_cfg._describe('name', instanceof=str, docstring='unique name for the job')
job_desc_cfg._branch('testset', strict=False)
job_desc_cfg._branch('hardware', value=hardware_cfg._deepcopy())


class TestsetJob(basejobs.ConfigJob):

    def make_jobcfg(self, expcfg, testset_name):
        self.jobcfg = job_desc_cfg._deepcopy()
        self.jobcfg.key  = (('testset',), testset_name, 0)
        self.jobcfg.name = self.context.relpath('testset.{}'.format(testset_name))

        self.jobcfg.testset = expcfg.testsets[testset_name]

        self.jobcfg.hardware.configfile  = './{}.ts.cfg'.format(testset_name)
        self.jobcfg.hardware.datafile    = './{}.ts.d'.format(testset_name)
        self.jobcfg.hardware.seed        = random.randint(0, 1000000)

    def prepare(self, args):
        expcfg, testset_name = args
        self.make_jobcfg(expcfg, testset_name)

        self.add_input_file(self.jobcfg.hardware.configfile,        full=True)
        self.add_output_file(self.jobcfg.hardware.datafile,         full=True)

        self.rep        = 0
        self._name      = self.jobcfg.name
        self.key        = self.jobcfg.key
        self.jobgroup.add_job(self)
