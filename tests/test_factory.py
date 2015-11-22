from __future__ import print_function, division, absolute_import
import os

import explorers
import environments.envs

import dotdot
import experiments

import scicfg

cfg = experiments.desc._deepcopy()
cfg.meta.user='fbenurea'
cfg.meta.rootpath='./rootpath/'
cfg.meta.run_exploration=True

cfg.exp.path = 'unit_tests/'
cfg.exp.prefix   = ('prefix',)
cfg.exp.repetitions = 3

cfg.exploration.steps = 1000
cfg.exploration.seeds = [45, 576, 1634]
cfg.exploration.ex_name  = 'random.motor'
cfg.exploration.explorer = explorers.RandomMotorExplorer.defcfg._deepcopy()
cfg.exploration.env_name = 'kin7_150'
cfg.exploration.env      = environments.envs.KinematicArm2D.defcfg._deepcopy()
cfg.exploration.deps     = ()

cfg.testsets = scicfg.SciConfig()
cfg.testsets['blabla.algorithm'] = 'fromfile'
cfg.testsets['blabla.input_file'] = os.path.abspath('./testset_kin')

cfg.tests.tnn = experiments.testnn_cfg._deepcopy()
cfg.tests.tnn.testset = 'blabla'
cfg.tests.tnn.kind = 'nn'
cfg.tests.tnn.ticks = [1, 2, 3, 4, 5, 10, 15, 20] + [i for i in range(25, cfg.exploration.steps+1, 25)]

cfg.tests.tcov = experiments.testcov_cfg._deepcopy()
cfg.tests.tcov.kind = 'cov'
cfg.tests.tcov.ticks = [1, 2, 3, 4, 5, 10, 15, 20] + [i for i in range(25, cfg.exploration.steps+1, 25)]
cfg.tests.tcov.buffer_size = 0.05


def reuse_ex(mb, p_reuse, algorithm='sensor_uniform', res=20, lrn_name='p0.05'):
    import learners
    assert 0 <= p_reuse <= 1

    r_ex          = explorers.MetaExplorer.defcfg._deepcopy()
    r_ex.eras     = (mb, None)
    r_ex.weights  = ((1-p_reuse, 0.0, p_reuse), (0.0, 1.0, 0.0))

    r_ex.ex_0                   = explorers.RandomMotorExplorer.defcfg._deepcopy()

    r_ex.ex_1                   = explorers.RandomGoalExplorer.defcfg._deepcopy()
    r_ex.ex_1.learner           = learners.MutateNNLearner.defcfg._deepcopy()
    r_ex.ex_1.learner.operator.name = 'uniform'
    r_ex.ex_1.learner.operator.d    = 0.05

    r_ex.ex_2                   = explorers.ReuseExplorer.defcfg._deepcopy()
    r_ex.ex_2.reuse.res         = res
    r_ex.ex_2.reuse.algorithm   = algorithm

    alg_str = '' if algorithm == 'sensor_uniform' else '.' + algorithm
    return 'reuse{}_{}_{}_{}_{}'.format(alg_str, mb, p_reuse, res, lrn_name), r_ex


tgt_cfg = cfg._deepcopy()
tgt_cfg.exp.path = 'unit_tests2/'

tgt_cfg.exploration.ex_name, tgt_cfg.exploration.explorer = reuse_ex(50, 0.5)
tgt_cfg.exploration.deps = (experiments.expkey(cfg),)
tgt_cfg.exp.prefix   = ('prefix', 'random.motor', 'kin7_150')


if __name__ == '__main__':
    experiments.run_exps([cfg, tgt_cfg])
