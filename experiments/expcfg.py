from __future__ import print_function, division, absolute_import

import collections
import numbers

import scicfg
import learners


desc = scicfg.SciConfig(strict=True)



    # Meta Config #

desc._describe('meta.user', instanceof=str,
               docstring='the name of the user')

desc._describe('meta.rootpath', instanceof=str,
               docstring='the path towards the data')

desc._describe('meta.module_names', instanceof=collections.Iterable,
               docstring='list of modules involved in the experiment, for tracking purposes',
               default=('experiments', 'clusterjobs', 'scicfg',
                        'learners', 'explorers', 'enviroments',
                        'scipy', 'numpy'))

desc._describe('meta.run_exploration', instanceof=bool, default=True,
               docstring='run the exploration')

desc._describe('meta.run_tests', instanceof=bool, default=False,
               docstring='run the tests')

desc._describe('meta.run_nns', instanceof=bool, default=False,
               docstring='run the nn tests')

desc._describe('meta.run_coverage', instanceof=bool, default=True,
               docstring='run the nn tests')


    # Provenance #

desc._describe('provenance.package_names', instanceof=collections.Iterable, default=(),
               docstring='python packages involved in the experiment (for tracking)')
desc._branch('provenance.code', strict=False)
desc._describe('provenance.check_dirty', instanceof=bool, default=True,
               docstring='Check if git repository are dirty')
desc._describe('provenance.check_continuity', instanceof=bool, default=True,
               docstring='Check if the provenance info (commits, platform, etc.) changes between executions of a same job')


    # Qsub #

desc._branch('qsub.resources')
desc.qsub.resources._strict(strict=False)


    # Experiment Config #

desc._describe('exp.path', instanceof=str,
               docstring='the root path of the experiment, relative to meta.rootpath')

desc._describe('exp.key', instanceof=collections.Iterable,
               docstring='the key for the experiment')

desc._describe('exp.prefix', instanceof=collections.Iterable,
               docstring='name of the experiment, as a list of strings')

desc._describe('exp.repetitions', instanceof=numbers.Integral,
               docstring='this job repetition')

desc._describe('exp.ex_name', instanceof=str,
               docstring='the explorer name for the experiment')

desc._describe('exp.env_name', instanceof=str,
               docstring='the environment name for the experiment')

desc._describe('exp.deps', instanceof=collections.Iterable, default=(),
               docstring='dependencies in case of reuse')

# desc._describe('exp.seeds.exploration', instanceof=collections.Iterable, default=(),
#                docstring='random seeds for exploration, for reproductibility')

# desc._describe('exp.s_noise', instanceof=numbers.Real, default = 0.0,
#                docstring='artificial, white, sensory noise')
#
# desc._describe('exp.m_noise', instanceof=numbers.Real, default = 0.0,
#                docstring='artificial, white, motor noise')


    # Job Config #

# desc._describe('job.key', instanceof=collections.Iterable,
#                docstring='this job repetition')
#
# desc._describe('job.rep', instanceof=numbers.Integral,
#                docstring='this job repetition')
#
# desc._describe('job.steps', instanceof=numbers.Integral,
#                docstring='the number of trials')

# desc._branch('job.env')


    # Hardware Config #

hardware_cfg = scicfg.SciConfig(strict=True)
hardware_cfg._describe('configfile',  instanceof=str, docstring='configuration file for exploration')
hardware_cfg._describe('datafile',    instanceof=str, docstring='configuration file for exploration')
hardware_cfg._describe('seed',        instanceof=numbers.Integral, docstring='random seed for repeatable experiments')
hardware_cfg._describe('logfile',     instanceof=str, docstring='the log file filepath')
hardware_cfg._describe('logs',        instanceof=bool, default=False, docstring='generate additional logs of the motor execution')
hardware_cfg._describe('autosave_period', instanceof=numbers.Integral, default=300, docstring='save data at regular intervals')


    # Exploration Config #

desc._branch('exploration.explorer', strict=False)
desc._branch('exploration.env', strict=False)
desc._describe('exploration.steps', instanceof=numbers.Integral, docstring='the number of trials')
desc._describe('exploration.seeds', instanceof=collections.Iterable, docstring='random seeds')


    # Testsets Configs #

desc._branch('testsets')

testset_cfg = scicfg.SciConfig(strict=True)
#testset_cfg._describe('hardware.testsetfile', instanceof=str, docstring='number of tests')
testset_cfg._describe('algorithm', instanceof=str, docstring='name of the algorithm to use to generate the testset')
testset_cfg._describe('size', instanceof=numbers.Integral, docstring='number of tests')


    # Tests Configs #

desc._branch('tests', strict=False)
