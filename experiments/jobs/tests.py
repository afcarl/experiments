import numbers
import collections
import random

import forest
import learners

from . import basejobs
from .keys import JobKey, expkey
from ..expcfg import hardware_cfg
from .exploration import ex_hardware_cfg


testkind_cfg = forest.Tree(strict=True)
testkind_cfg._describe('kind', instanceof=str)
testkind_cfg._describe('ticks', instanceof=collections.Iterable)

testinv_cfg = testkind_cfg._deepcopy()
testinv_cfg._describe('testset', instanceof=str, docstring='name of the testset')
testinv_cfg._describe('rep', instanceof=numbers.Integral, default=-1)

learner_cfg = learners.ModelLearner.defcfg._copy(deep=True)
learner_cfg.models.fwd = 'ES-LWLR'
learner_cfg.models.inv = 'L-BFGS-B'
testinv_cfg._branch('learner', value=learner_cfg)

testnn_cfg = testkind_cfg._deepcopy()
testnn_cfg._describe('testset', instanceof=str, docstring='name of the testset')

testcov_cfg = testkind_cfg._deepcopy()
testcov_cfg._describe('buffer_size', instanceof=numbers.Real)

job_desc_cfgs = {'cov': testcov_cfg,
                 'nn':   testnn_cfg,
                 'inv': testinv_cfg}


job_desc_cfg = forest.Tree(strict=True)
job_desc_cfg._describe('key', instanceof=collections.Iterable, docstring='unique key for the job')
#job_desc_cfg._describe('key', instanceof=numbers.Integer, docstring='repetition number')
job_desc_cfg._describe('name', instanceof=str, docstring='unique name for the job')
job_desc_cfg._describe('testname', instanceof=str, docstring='name of the test')
job_desc_cfg._branch('test', strict=False)
# del job_desc_cfg.exploration.seeds
job_desc_cfg._branch('hardware', value=hardware_cfg._deepcopy())
job_desc_cfg._branch('hardware.testset', value=hardware_cfg._deepcopy())
job_desc_cfg._branch('hardware.exploration', value=ex_hardware_cfg._deepcopy())


class TestJob(basejobs.ConfigJob):

    def make_jobcfg(self, expcfg, ex_job, testname):
        self.jobkey =JobKey(('test', testname), expkey(expcfg), ex_job.rep)

        self.jobcfg = job_desc_cfg._deepcopy()
        self.jobcfg.key  = self.jobkey.key
        self.jobcfg.name = self.jobkey.name
        self.jobcfg.testname = testname

        self.jobcfg.test = expcfg.tests[testname]

        if 'testset' in self.jobcfg.test:
            testset_job = self.jobgroup.jobs_byname[self.context.relpath('testset.{}'.format(self.jobcfg.test.testset))]
            self.jobcfg.hardware.testset = testset_job.jobcfg.hardware._deepcopy()

        self.jobcfg.hardware.exploration = ex_job.jobcfg.hardware._deepcopy()
        self.jobcfg.hardware.datafile    = self.jobkey.filepath + '.d'
        self.jobcfg.hardware.configfile  = self.jobkey.filepath + '.cfg'
        self.jobcfg.hardware.logfile     = self.jobkey.filepath + '.log'
        self.jobcfg.hardware.seed        = random.randint(0, 100000000000)

    def prepare(self, args):
        expcfg, ex_job, testname = args
        self.make_jobcfg(expcfg, ex_job, testname)

        self.add_input_file(self.jobcfg.hardware.configfile, full=True)
        if 'datafile' in self.jobcfg.hardware.testset:
            self.add_input_file(self.jobcfg.hardware.testset.datafile, full=True)

        if self.jobcfg.test.kind == 'inv':
            self.add_input_file(self.jobcfg.hardware.exploration.datafile, full=True)
        else:
            self.add_input_file(self.jobcfg.hardware.exploration.sensoryfile, full=True)
        self.add_output_file(self.jobcfg.hardware.datafile, full=True)
        self.add_output_file(self.jobcfg.hardware.datafile+'.done', full=True)

        self._finalize()
