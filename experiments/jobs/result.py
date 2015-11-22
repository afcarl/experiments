import numbers
import collections
import random

import scicfg
import learners

from . import basejobs
from .keys import JobKey, expkey
from ..expcfg import hardware_cfg
from .exploration import ex_hardware_cfg


job_desc_cfg = scicfg.SciConfig(strict=True)
job_desc_cfg._describe('key', instanceof=collections.Iterable, docstring='unique key for the job')
job_desc_cfg._describe('name', instanceof=str, docstring='unique name for the job')
job_desc_cfg._describe('rep', instanceof=numbers.Integral, docstring='number of tests')
job_desc_cfg._describe('testname', instanceof=str, docstring='name of the test')
job_desc_cfg._branch('test', strict=False)
job_desc_cfg._branch('hardware', value=hardware_cfg._deepcopy())
job_desc_cfg._describe('hardware.testfiles', instanceof=collections.Iterable)


class ResultJob(basejobs.ConfigJob):

    def make_jobcfg(self, expcfg, testname):
        rep = expcfg.exp.repetitions
        self.jobkey = JobKey(('result', testname), expkey(expcfg), rep)

        self.jobcfg = job_desc_cfg._deepcopy()
        self.jobcfg.key  = self.jobkey.key
        self.jobcfg.name = self.jobkey.name
        self.jobcfg.rep  = rep
        self.jobcfg.testname = testname
        self.jobcfg.test = expcfg.tests[testname]

        self.jobcfg.hardware.testfiles = []
        for i in range(rep):
            testkey = JobKey(('test', testname), expkey(expcfg), i)
            test_job = self.jobgroup.jobs_byname[testkey.name]
            self.jobcfg.hardware.testfiles.append(test_job.jobcfg.hardware.datafile)

        self.jobcfg.hardware.datafile    = self.jobkey.filepath + '.d'
        self.jobcfg.hardware.configfile  = self.jobkey.filepath + '.cfg'

    def prepare(self, args):
        expcfg, testname = args
        self.make_jobcfg(expcfg, testname)

        self.add_input_file(self.jobcfg.hardware.configfile, full=True)
        for testfile in self.jobcfg.hardware.testfiles:
            self.add_input_file(testfile, full=True)

        self.add_output_file(self.jobcfg.hardware.datafile, full=True)
        #`self.add_output_file(self.jobcfg.hardware.datafile+'.done', full=True)

        self._finalize()
