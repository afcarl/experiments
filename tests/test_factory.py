from __future__ import print_function, division, absolute_import

import explorers
import environments.envs

import dotdot
import experiments


cfg = experiments.desc._deepcopy()
cfg.meta.user='fbenurea'
cfg.meta.rootpath='./rootpath/'
cfg.meta.run_exploration=True

cfg.exp.path = 'unit_tests/factory/'
cfg.exp.prefix   = ('prefix',)
cfg.exp.repetitions = 3

cfg.exploration.steps = 1000
cfg.exploration.seeds = [45, 576, 1634]
cfg.exploration.ex_name  = 'random.motor'
cfg.exploration.explorer = explorers.RandomMotorExplorer.defcfg._deepcopy()
cfg.exploration.env_name = 'kin7_150'
cfg.exploration.env      = environments.envs.KinematicArm2D.defcfg._deepcopy()
cfg.exploration.deps     = ()

cfg.tests.tcov = experiments.testcov_cfg._deepcopy()
cfg.tests.tcov.kind = 'cov'
cfg.tests.tcov.ticks = [i+1 for i in range(0, 1000, 25)]
cfg.tests.tcov.buffer_size = 0.05


if __name__ == '__main__':
    experiments.run_exp(cfg)
#    grp.prepare_hds()

#
#     # Tests Configs #
#
# desc._branch('tests', strict=False)
# desc._branch('testsets', strict=False)
#
# test_cfg = forest.Tree()
# test_cfg._describe('kind', instanceof=str)
# test_cfg._describe('cfg', instanceof=str)
#
# testset_cfg = forest.Tree()
# #testset_cfg._describe('hardware.testsetfile', instanceof=str, docstring='number of tests')
# testset_cfg._describe('algorithm', instanceof=str, docstring='name of the algorithm to use to generate the testset')
# testset_cfg._describe('size', instanceof=numbers.Integral, docstring='number of tests')
#
# testkind_cfg = forest.Tree()

# testkind_cfg._describe('ticks', instanceof=collections.Iterable)
#
# testinv_cfg = testkind_cfg._deepcopy()
# testinv_cfg._describe('testset_name', docstring='name of the testset')
# testinv_cfg._describe('rep', instanceof=numbers.Integral, default=())
#
# learner_cfg = learners.ModelLearner.defcfg._copy(deep=True)
# learner_cfg.models.fwd = 'ES-LWLR'
# learner_cfg.models.inv = 'L-BFGS-B'
# testinv_cfg._branch('learner', value=learner_cfg)
#
# testnn_cfg = testkind_cfg._deepcopy()
# testnn_cfg._describe('testset_name', docstring='name of the testset')
#
# testcov_cfg = testkind_cfg._deepcopy()
# testcov_cfg._describe('buffer_size', instanceof=numbers.Real)
